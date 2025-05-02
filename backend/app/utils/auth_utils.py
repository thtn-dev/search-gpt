import base64
import logging
import httpx
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from typing import Dict, Any, Tuple

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.utils import int_to_bytes

from app.config.settings import settings
from app.schemas.auth_schemas import AuthProvider, NextAuthSigninPayload, VerifiedUserData
logger = logging.getLogger(__name__)
async def verify_google_id_token(google_token: str) -> VerifiedUserData:
    try:
        idinfo = id_token.verify_oauth2_token(
            google_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        return VerifiedUserData(
            provider=AuthProvider.GOOGLE,
            provider_key=idinfo['sub'],
            email=idinfo.get('email'),
            name=idinfo.get('name'),
            picture=idinfo.get('picture')
        )
    except ValueError as e:
        print(f"Google Token verification error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Google token: {e}")
    except Exception as e:
        print(f"Unexpected error verifying Google token: {e}")
        raise HTTPException(status_code=500, detail="Error verifying Google token.")

async def verify_github_access_token(github_access_token: str) -> VerifiedUserData:
    user_api_url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {github_access_token}"}
    async with httpx.AsyncClient() as client:
        try:
            user_response = await client.get(user_api_url, headers=headers)
            # GitHub trả về 401 nếu token không hợp lệ/hết hạn
            if user_response.status_code == 401:
                 raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired GitHub token")
            user_response.raise_for_status() # Raise lỗi cho các status code khác (5xx, 403...)
            user_info = user_response.json()

            # Cố gắng lấy email (có thể cần gọi /user/emails nếu scope user:email được cấp)
            primary_email = user_info.get('email')
            # if not primary_email: ... logic gọi /user/emails ...

            return VerifiedUserData(
                provider=AuthProvider.GITHUB,
                provider_key=str(user_info['id']), # ID là số, chuyển sang string
                email=primary_email,
                name=user_info.get('name'),
                picture=user_info.get('avatar_url')
            )
        except httpx.HTTPStatusError as e:
            print(f"GitHub API HTTP error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error fetching GitHub user info: {e.response.status_code}")
        except Exception as e:
            print(f"Unexpected error fetching GitHub user info: {e}")
            raise HTTPException(status_code=500, detail="Unexpected error fetching GitHub user info")
        

def base64url_decode(input):
    """Helper to decode base64url string."""
    rem = len(input) % 4
    if rem > 0:
        input += '=' * (4 - rem)
    return base64.urlsafe_b64decode(input)

# --- Cache cho Khóa Công Khai (đối tượng cryptography) và Issuer ---
# Cache sẽ lưu tuple: (RSAPublicKey, expected_issuer)
_microsoft_public_key_cache: Dict[str, Tuple[rsa.RSAPublicKey, str]] = {}

async def get_microsoft_public_key(kid: str, tenant_id: str) -> Tuple[rsa.RSAPublicKey, str]:
    """
    Fetches the appropriate RSA public key object from Microsoft's JWKS endpoint
    and the expected issuer from the OIDC configuration. Caches the result.
    Returns a tuple (RSAPublicKey, expected_issuer).
    """
    # Kiểm tra cache trước
    if kid in _microsoft_public_key_cache:
        logger.debug(f"Using cached public key for kid: {kid}")
        return _microsoft_public_key_cache[kid]

    oidc_config_url = f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration"
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Fetching Microsoft OIDC config from: {oidc_config_url}")
            oidc_response = await client.get(oidc_config_url)
            oidc_response.raise_for_status()
            oidc_config = oidc_response.json()
            jwks_uri = oidc_config.get("jwks_uri")
            expected_issuer = oidc_config.get("issuer") # Lấy issuer từ config
            if not jwks_uri or not expected_issuer:
                raise ValueError("Could not find JWKS URI or Issuer in OIDC config")

            logger.info(f"Fetching Microsoft JWKS from: {jwks_uri}")
            jwks_response = await client.get(jwks_uri)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()

            public_key: rsa.RSAPublicKey | None = None
            for key_dict in jwks.get("keys", []):
                if key_dict.get("kid") == kid and key_dict.get("kty") == "RSA":
                    # --- Chuyển đổi JWK (RSA) sang đối tượng RSAPublicKey của cryptography ---
                    n_b64 = key_dict.get("n")
                    e_b64 = key_dict.get("e")
                    if not n_b64 or not e_b64:
                        logger.warning(f"JWK with kid {kid} is missing 'n' or 'e'. Skipping.")
                        continue

                    # Decode base64url-encoded n và e
                    n_int = int.from_bytes(base64url_decode(n_b64), 'big')
                    e_int = int.from_bytes(base64url_decode(e_b64), 'big')

                    # Tạo đối tượng public numbers
                    public_numbers = rsa.RSAPublicNumbers(e=e_int, n=n_int)
                    # Tạo đối tượng public key
                    public_key = public_numbers.public_key()
                    logger.info(f"Successfully constructed RSA public key for kid: {kid}")
                    break # Tìm thấy key phù hợp

            if public_key:
                # Lưu cả key object và issuer vào cache
                _microsoft_public_key_cache[kid] = (public_key, expected_issuer)
                return public_key, expected_issuer
            else:
                 # Xóa cache nếu không tìm thấy key để tránh cache lỗi
                 if kid in _microsoft_public_key_cache:
                      del _microsoft_public_key_cache[kid]
                 raise ValueError(f"RSA public key with kid '{kid}' not found in JWKS.")

        except httpx.RequestError as e:
             logger.error(f"Network error fetching Microsoft OIDC/JWKS: {e}")
             raise HTTPException(status_code=503, detail="Network error connecting to Microsoft for keys")
        except httpx.HTTPStatusError as e:
             logger.error(f"HTTP error fetching Microsoft OIDC/JWKS: {e.response.status_code} - {e.response.text}")
             raise HTTPException(status_code=503, detail="Could not fetch Microsoft signing keys")
        except Exception as e:
            logger.error(f"Error fetching/constructing Microsoft public key: {e}", exc_info=True)
            # Xóa cache nếu có lỗi
            if kid in _microsoft_public_key_cache:
                 del _microsoft_public_key_cache[kid]
            raise HTTPException(status_code=500, detail="Error processing Microsoft signing keys")


async def verify_microsoft_id_token(ms_token: str) -> VerifiedUserData:
    """Verifies Microsoft ID Token using PyJWT and returns standardized user info."""
    try:
        # Lấy kid từ header mà không cần xác thực trước
        unverified_header = jwt.get_unverified_header(ms_token)
        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg") # Lấy thuật toán từ header
        if not kid:
            raise ValueError("Missing 'kid' in token header")
        if not alg or alg != "RS256": # Đảm bảo thuật toán là RS256
             raise ValueError(f"Unsupported algorithm: {alg}. Expected RS256.")


        # Lấy đối tượng khóa công khai cryptography và issuer mong đợi
        public_key_obj, expected_issuer = await get_microsoft_public_key(kid, settings.MICROSOFT_TENANT_ID)

        logger.debug(f"Attempting to decode Microsoft token using public key object for kid: {kid}")

        # --- Sử dụng PyJWT để decode ---
        payload = jwt.decode(
            ms_token,
            key=public_key_obj, # Truyền đối tượng khóa cryptography
            algorithms=["RS256"], # Chỉ định thuật toán
            audience=settings.MICROSOFT_CLIENT_ID, # Kiểm tra audience
            issuer=expected_issuer # Kiểm tra issuer
            # options={"verify_signature": True, "verify_exp": True, ...} # Các tùy chọn mặc định thường là đủ
        )

        # Kiểm tra 'tid' nếu tenant không phải 'common'
        if settings.MICROSOFT_TENANT_ID != "common" and payload.get('tid') != settings.MICROSOFT_TENANT_ID:
             logger.warning(f"Tenant ID mismatch. Expected {settings.MICROSOFT_TENANT_ID}, got {payload.get('tid')}")
             raise ValueError("Incorrect tenant ID in token")
        logger.info(f"Microsoft token verified successfully for kid: {kid}")
        logger.info(f"Token payload: {payload}")
        # Trích xuất thông tin user chuẩn hóa
        return VerifiedUserData(
            provider=AuthProvider.MICROSOFT,
            provider_key=payload['sub'], # Object ID trong Azure AD
            email=payload.get('email') or payload.get('preferred_username'),
            name=payload.get('name'),
            picture=None
        )
    # --- Bắt các lỗi cụ thể của PyJWT ---
    except jwt.ExpiredSignatureError as e:
        logger.warning(f"Microsoft token has expired: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Microsoft token has expired")
    except jwt.InvalidAudienceError as e:
        logger.warning(f"Invalid audience in Microsoft token: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid audience in Microsoft token")
    except jwt.InvalidIssuerError as e:
         logger.warning(f"Invalid issuer in Microsoft token: {e}")
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid issuer in Microsoft token")
    except jwt.DecodeError as e:
         logger.error(f"Error decoding Microsoft token (PyJWT): {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Microsoft token: Decode error - {e}")
    except jwt.PyJWKClientError as e: # Lỗi liên quan đến việc lấy key (mặc dù ta tự lấy)
         logger.error(f"PyJWKClientError related error: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="Error related to JWK processing")
    # --- Các lỗi khác ---
    except ValueError as e:
         logger.error(f"Microsoft Token verification value error: {e}")
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Microsoft token format or value: {e}")
    except HTTPException as e:
         raise e # Re-raise các HTTPException từ get_microsoft_public_key
    except Exception as e:
        logger.error(f"Unexpected error verifying Microsoft token: {e}", exc_info=True)
        if kid and kid in _microsoft_public_key_cache: # Xóa cache nếu có lỗi lạ
            del _microsoft_public_key_cache[kid]
        raise HTTPException(status_code=500, detail="Internal error verifying Microsoft token.")


# --- Dispatcher ---
async def verify_identity_from_nextauth(payload: NextAuthSigninPayload) -> VerifiedUserData:
    """Verifies identity based on provider and token type."""
    if payload.provider == AuthProvider.GOOGLE and payload.id_token:
        return await verify_google_id_token(payload.id_token)
    elif payload.provider == AuthProvider.MICROSOFT and payload.id_token:
        return await verify_microsoft_id_token(payload.id_token)
    elif payload.provider == AuthProvider.GITHUB and payload.access_token:
        return await verify_github_access_token(payload.access_token)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing appropriate token for provider '{payload.provider.value}'"
        )

