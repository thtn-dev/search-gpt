import httpx
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from typing import Dict, Any

import jwt

from app.config.settings import settings
from app.schemas.auth_schemas import AuthProvider, NextAuthSigninPayload, VerifiedUserData

async def verify_google_id_token(google_token: str) -> VerifiedUserData:
    try:
        idinfo = id_token.verify_oauth2_token(
            google_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        return VerifiedUserData(
            provider=AuthProvider.GOOGLE,
            provider_id=idinfo['sub'],
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
                provider_id=str(user_info['id']), # ID là số, chuyển sang string
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
        

_microsoft_jwks_cache: Dict[str, Dict] = {}

async def get_microsoft_jwk(kid: str, tenant_id: str) -> Dict[str, Any]:
    # Kiểm tra cache trước
    if kid in _microsoft_jwks_cache:
        return _microsoft_jwks_cache[kid]

    oidc_config_url = f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration"
    async with httpx.AsyncClient() as client:
        try:
            print(f"Fetching Microsoft OIDC config from: {oidc_config_url}")
            oidc_response = await client.get(oidc_config_url)
            oidc_response.raise_for_status()
            jwks_uri = oidc_response.json().get("jwks_uri")
            issuer = oidc_response.json().get("issuer") # Lấy issuer thực tế từ config
            if not jwks_uri or not issuer:
                raise ValueError("Could not find JWKS URI or Issuer in OIDC config")

            print(f"Fetching Microsoft JWKS from: {jwks_uri}")
            jwks_response = await client.get(jwks_uri)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()

            # Cập nhật cache
            _microsoft_jwks_cache.clear() # Xóa cache cũ
            found_key = None
            for key in jwks.get("keys", []):
                key_kid = key.get("kid")
                if key_kid:
                    _microsoft_jwks_cache[key_kid] = key # Cache tất cả các key tìm thấy
                    if key_kid == kid:
                        found_key = key

            if found_key:
                # Lưu issuer vào cache cùng với key để sử dụng khi decode
                found_key["issuer"] = issuer # Thêm issuer vào thông tin key đã cache
                return found_key
            else:
                 raise ValueError(f"Public key with kid '{kid}' not found in JWKS.")

        except httpx.RequestError as e:
             print(f"Network error fetching Microsoft OIDC/JWKS: {e}")
             raise HTTPException(status_code=503, detail="Network error connecting to Microsoft for keys")
        except httpx.HTTPStatusError as e:
             print(f"HTTP error fetching Microsoft OIDC/JWKS: {e.response.status_code} - {e.response.text}")
             raise HTTPException(status_code=503, detail="Could not fetch Microsoft signing keys")
        except Exception as e:
            print(f"Error fetching/finding Microsoft JWK: {e}")
            _microsoft_jwks_cache.clear() # Xóa cache nếu có lỗi
            raise HTTPException(status_code=500, detail="Error processing Microsoft signing keys")

async def verify_microsoft_id_token(ms_token: str) -> VerifiedUserData:
    try:
        unverified_header = jwt.get_unverified_header(ms_token)
        kid = unverified_header.get("kid")
        if not kid: raise ValueError("Missing 'kid'")

        jwk_with_issuer = await get_microsoft_jwk(kid, settings.MICROSOFT_TENANT_ID)
        public_key = jwk_with_issuer # jwk đã chứa key
        expected_issuer = jwk_with_issuer.get("issuer") # Lấy issuer đã cache

        if not expected_issuer:
            # Fallback nếu cache bị lỗi (không nên xảy ra)
            raise ValueError("Issuer not found in cached JWK")

        payload = jwt.decode(
            ms_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.MICROSOFT_CLIENT_ID,
            issuer=expected_issuer # Sử dụng issuer lấy từ OIDC config
        )

        # Kiểm tra 'tid' nếu tenant không phải 'common' và cần đảm bảo đúng tenant
        if settings.MICROSOFT_TENANT_ID != "common" and payload.get('tid') != settings.MICROSOFT_TENANT_ID:
             raise ValueError(f"Incorrect tenant ID. Expected {settings.MICROSOFT_TENANT_ID}, got {payload.get('tid')}")

        return VerifiedUserData(
            provider=AuthProvider.MICROSOFT,
            provider_id=payload['oid'], # Object ID
            email=payload.get('email') or payload.get('preferred_username'),
            name=payload.get('name'),
            picture=None # Thường không có trong ID token MS
        )
    except jwt.PyJWTError as e:
        print(f"Microsoft Token JWT validation error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Microsoft token: {e}")
    except ValueError as e:
         print(f"Microsoft Token verification value error: {e}")
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Microsoft token format: {e}")
    except Exception as e:
        print(f"Unexpected error verifying Microsoft token: {e}")
        # Xóa cache nếu có lỗi 
        _microsoft_jwks_cache.clear()
        raise HTTPException(status_code=500, detail="Error verifying Microsoft token.")


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

