"""
Authentication utility functions for verifying tokens from various providers.
"""

import base64
import logging
from typing import Dict, Tuple

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config.settings import settings
from app.schemas.auth_schemas import (
    AuthProvider,
    NextAuthSigninPayload,
    VerifiedUserData,
)

logger = logging.getLogger(__name__)


async def verify_google_id_token(google_token: str) -> VerifiedUserData:
    """Verifies a Google ID token and returns standardized user data."""
    try:
        idinfo = id_token.verify_oauth2_token(
            google_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        return VerifiedUserData(
            provider=AuthProvider.GOOGLE,
            provider_key=idinfo['sub'],
            email=idinfo.get('email'),
            name=idinfo.get('name'),
            picture=idinfo.get('picture'),
        )
    except ValueError as e:
        logger.error('Google Token verification value error: %s', e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Invalid Google token: {e}',  # f-string in HTTPException detail is fine
        ) from e
    except Exception as e:
        logger.error('Unexpected error verifying Google token: %s', e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Error verifying Google token.',
        ) from e


async def verify_github_access_token(github_access_token: str) -> VerifiedUserData:
    """Verifies a GitHub access token by fetching user info."""
    user_api_url = 'https://api.github.com/user'
    headers = {'Authorization': f'Bearer {github_access_token}'}
    async with httpx.AsyncClient() as client:
        try:
            user_response = await client.get(user_api_url, headers=headers)
            if user_response.status_code == 401:
                logger.warning(
                    'GitHub token is invalid or expired (401). Token: %s*****',
                    github_access_token[:5],
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid or expired GitHub token',
                )
            user_response.raise_for_status()
            user_info = user_response.json()

            primary_email = user_info.get('email')
            # if not primary_email:
            # logger.debug("Primary email not found directly for GitHub user %s, may need to query /user/emails", user_info.get('login'))
            # ... logic to call /user/emails ...

            return VerifiedUserData(
                provider=AuthProvider.GITHUB,
                provider_key=str(user_info['id']),
                email=primary_email,
                name=user_info.get('name'),
                picture=user_info.get('avatar_url'),
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                'GitHub API HTTP error: %s - %s. Token: %s*****',
                e.response.status_code,
                e.response.text,
                github_access_token[:5],
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f'Error fetching GitHub user info: {e.response.status_code}',
            ) from e
        except Exception as e:
            logger.error(
                'Unexpected error fetching GitHub user info. Token: %s*****. Error: %s',
                github_access_token[:5],
                e,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Unexpected error fetching GitHub user info',
            ) from e


def base64url_decode(input_str: str) -> bytes:
    """Helper to decode base64url string."""
    rem = len(input_str) % 4
    if rem > 0:
        input_str += '=' * (4 - rem)
    return base64.urlsafe_b64decode(input_str)


_microsoft_public_key_cache: Dict[str, Tuple[rsa.RSAPublicKey, str]] = {}


# --- Helper functions for get_microsoft_public_key ---
async def _fetch_microsoft_oidc_config(
    client: httpx.AsyncClient, oidc_config_url: str, tenant_id: str
) -> Tuple[str, str]:
    """Fetches OIDC config and returns jwks_uri and expected_issuer."""
    logger.info('Fetching Microsoft OIDC config from: %s', oidc_config_url)
    oidc_response = await client.get(oidc_config_url)
    oidc_response.raise_for_status()  # Let caller handle HTTPStatusError
    oidc_config = oidc_response.json()
    jwks_uri = oidc_config.get('jwks_uri')
    expected_issuer = oidc_config.get('issuer')
    if not jwks_uri or not expected_issuer:
        logger.error(
            'Could not find JWKS URI or Issuer in OIDC config for tenant %s. URI: %s, Issuer: %s',
            tenant_id,
            jwks_uri,
            expected_issuer,
        )
        raise ValueError('Could not find JWKS URI or Issuer in OIDC config')
    return jwks_uri, expected_issuer


async def _fetch_microsoft_jwks(client: httpx.AsyncClient, jwks_uri: str) -> Dict:
    """Fetches JWKS from the given URI."""
    logger.info('Fetching Microsoft JWKS from: %s', jwks_uri)
    jwks_response = await client.get(jwks_uri)
    jwks_response.raise_for_status()  # Let caller handle HTTPStatusError
    return jwks_response.json()


def _construct_rsa_public_key_from_jwk_data(
    key_dict: Dict, target_kid: str
) -> rsa.RSAPublicKey | None:
    """Constructs an RSA public key from JWK data if 'n' and 'e' are present."""
    n_b64 = key_dict.get('n')
    e_b64 = key_dict.get('e')
    if not n_b64 or not e_b64:
        logger.warning("JWK with kid %s is missing 'n' or 'e'.", target_kid)
        return None

    try:
        n_int = int.from_bytes(base64url_decode(n_b64), 'big')
        e_int = int.from_bytes(base64url_decode(e_b64), 'big')
    except (ValueError, TypeError) as decode_err:
        logger.error('Error decoding n/e for JWK kid %s: %s', target_kid, decode_err)
        return None

    public_numbers = rsa.RSAPublicNumbers(e=e_int, n=n_int)
    public_key = public_numbers.public_key()
    logger.info('Successfully constructed RSA public key for kid: %s', target_kid)
    return public_key


# --- End of helper functions ---


async def get_microsoft_public_key(
    kid: str, tenant_id: str
) -> Tuple[rsa.RSAPublicKey, str]:
    """
    Fetches the appropriate RSA public key object from Microsoft's JWKS endpoint
    and the expected issuer from the OIDC configuration. Caches the result.
    Returns a tuple (RSAPublicKey, expected_issuer).
    """
    if kid in _microsoft_public_key_cache:
        logger.debug('Using cached public key for kid: %s', kid)
        return _microsoft_public_key_cache[kid]

    oidc_config_url = f'https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration'
    public_key_obj: rsa.RSAPublicKey | None = None
    expected_issuer: str | None = None

    try:
        async with httpx.AsyncClient() as client:
            jwks_uri, expected_issuer = await _fetch_microsoft_oidc_config(
                client, oidc_config_url, tenant_id
            )
            jwks = await _fetch_microsoft_jwks(client, jwks_uri)

            for key_data in jwks.get('keys', []):
                if key_data.get('kid') == kid and key_data.get('kty') == 'RSA':
                    public_key_obj = _construct_rsa_public_key_from_jwk_data(
                        key_data, kid
                    )
                    if public_key_obj:
                        break  # Found and constructed key

            if public_key_obj and expected_issuer:
                _microsoft_public_key_cache[kid] = (public_key_obj, expected_issuer)
                return public_key_obj, expected_issuer

            # If key not found or issuer was missing (though helper should raise for issuer)
            logger.error(
                "RSA public key with kid '%s' not found in JWKS or expected issuer is missing.",
                kid,
            )
            raise ValueError(
                f"RSA public key with kid '{kid}' not found or issuer missing after OIDC/JWKS fetch."
            )

    except httpx.RequestError as e:
        logger.error(
            'Network error fetching Microsoft OIDC/JWKS for tenant %s, kid %s: %s',
            tenant_id,
            kid,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Network error connecting to Microsoft for keys',
        ) from e
    except httpx.HTTPStatusError as e:
        logger.error(
            'HTTP error fetching Microsoft OIDC/JWKS for tenant %s, kid %s: Status %s - %s',
            tenant_id,
            kid,
            e.response.status_code,
            e.response.text,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Could not fetch Microsoft signing keys due to HTTP error',
        ) from e
    except ValueError as e:  # Catches ValueErrors from helpers or this function's logic
        logger.error(
            'ValueError during Microsoft key retrieval for tenant %s, kid %s: %s',
            tenant_id,
            kid,
            e,
        )
        if kid in _microsoft_public_key_cache:
            del _microsoft_public_key_cache[kid]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Invalid configuration or data for Microsoft signing keys: {e}',
        ) from e
    except Exception as e:
        logger.error(
            'Unexpected error fetching/constructing Microsoft public key for tenant %s, kid %s: %s',
            tenant_id,
            kid,
            e,
            exc_info=True,
        )
        if kid in _microsoft_public_key_cache:
            del _microsoft_public_key_cache[kid]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Error processing Microsoft signing keys',
        ) from e


# --- Helper for verify_microsoft_id_token ---
def _parse_ms_token_header(ms_token: str) -> Tuple[str, str]:
    """Parses and validates 'kid' and 'alg' from token header."""
    try:
        unverified_header = jwt.get_unverified_header(ms_token)
    except (
        jwt.DecodeError
    ) as e:  # Handles cases where token is malformed and header can't be read
        logger.error(
            'Could not decode Microsoft token header: %s. Token: %s*****',
            e,
            ms_token[:20],
        )
        raise ValueError(f'Malformed token header: {e}') from e

    kid = unverified_header.get('kid')
    alg = unverified_header.get('alg')
    if not kid:
        logger.error(
            "Missing 'kid' in Microsoft token header. Token: %s*****", ms_token[:20]
        )
        raise ValueError("Missing 'kid' in token header")
    if not alg or alg != 'RS256':
        logger.error(
            "Unsupported algorithm '%s' in Microsoft token. Expected RS256. Kid: %s",
            alg,
            kid,
        )
        raise ValueError(f'Unsupported algorithm: {alg}. Expected RS256.')
    return kid, alg


# --- End of helper ---

_JWT_ERROR_TO_HTTP_DETAIL = {
    jwt.ExpiredSignatureError: 'Microsoft token has expired',
    jwt.InvalidAudienceError: 'Invalid audience in Microsoft token',
    jwt.InvalidIssuerError: 'Invalid issuer in Microsoft token',
}


async def verify_microsoft_id_token(ms_token: str) -> VerifiedUserData:
    """Verifies Microsoft ID Token using PyJWT and returns standardized user info."""
    kid = None  # Initialize kid to handle potential errors before it's set
    try:
        kid, _ = _parse_ms_token_header(
            ms_token
        )  # alg from header not directly used after this

        public_key_obj, expected_issuer = await get_microsoft_public_key(
            kid, settings.MICROSOFT_TENANT_ID
        )

        logger.debug(
            'Attempting to decode Microsoft token using public key object for kid: %s',
            kid,
        )

        payload = jwt.decode(
            ms_token,
            key=public_key_obj,
            algorithms=['RS256'],
            audience=settings.MICROSOFT_CLIENT_ID,
            issuer=expected_issuer,
        )

        if (
            settings.MICROSOFT_TENANT_ID != 'common'
            and payload.get('tid') != settings.MICROSOFT_TENANT_ID
        ):
            logger.warning(
                'Tenant ID mismatch for kid %s. Expected %s, got %s',
                kid,
                settings.MICROSOFT_TENANT_ID,
                payload.get('tid'),
            )
            raise ValueError('Incorrect tenant ID in token')

        logger.info(
            'Microsoft token verified successfully for kid: %s, user: %s',
            kid,
            payload.get('sub'),
        )
        # logger.debug("Token payload for kid %s: %s", kid, payload) # Uncomment if needed, be mindful of PII

        return VerifiedUserData(
            provider=AuthProvider.MICROSOFT,
            provider_key=payload['sub'],
            email=payload.get('email') or payload.get('preferred_username'),
            name=payload.get('name'),
            picture=None,
        )
    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidAudienceError,
        jwt.InvalidIssuerError,
    ) as e:
        detail = _JWT_ERROR_TO_HTTP_DETAIL.get(
            type(e), 'Invalid Microsoft token (unspecified JWT error)'
        )
        logger.warning('%s for kid %s: %s', detail, kid, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=detail
        ) from e
    except (
        jwt.DecodeError
    ) as e:  # Specific handling for DecodeError if not caught by _parse_ms_token_header
        logger.error(
            'Error decoding Microsoft token (PyJWT) for kid %s: %s',
            kid,
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Invalid Microsoft token: Decode error - {e}',
        ) from e
    except (
        jwt.PyJWKClientError
    ) as e:  # Should not happen with manual key fetching but included for completeness
        logger.error(
            'PyJWKClientError related error for kid %s: %s', kid, e, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Error related to JWK processing',
        ) from e
    except ValueError as e:  # Catches ValueErrors from our logic (e.g., _parse_ms_token_header, tenant check)
        logger.error('Microsoft Token verification value error for kid %s: %s', kid, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Invalid Microsoft token format or value: {e}',
        ) from e
    except HTTPException as e:  # Re-raise HTTPExceptions from get_microsoft_public_key
        raise e
    except Exception as e:
        logger.error(
            'Unexpected error verifying Microsoft token for kid %s: %s',
            kid,
            e,
            exc_info=True,
        )
        if (
            kid and kid in _microsoft_public_key_cache
        ):  # Clean cache on unexpected error
            del _microsoft_public_key_cache[kid]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal error verifying Microsoft token.',
        ) from e


async def verify_identity_from_nextauth(
    payload: NextAuthSigninPayload,
) -> VerifiedUserData:
    """Verifies identity based on provider and token type from NextAuth.js callback."""
    logger.info('Verifying identity for provider: %s', payload.provider.value)

    if payload.provider == AuthProvider.GOOGLE and payload.id_token:
        return await verify_google_id_token(payload.id_token)
    # Changed from elif to if due to R1705 (no-else-return)
    if payload.provider == AuthProvider.MICROSOFT and payload.id_token:
        return await verify_microsoft_id_token(payload.id_token)
    # Changed from elif to if due to R1705 (no-else-return)
    if payload.provider == AuthProvider.GITHUB and payload.access_token:
        return await verify_github_access_token(payload.access_token)

    # This block is effectively the 'else' case
    logger.warning(
        "Missing appropriate token for provider '%s'. ID token provided: %s, Access token provided: %s",
        payload.provider.value,
        bool(payload.id_token),
        bool(payload.access_token),
    )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Missing appropriate token for provider '{payload.provider.value}'",
    )
