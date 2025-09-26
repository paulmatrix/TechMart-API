"""
Auth0 JWT verification utility for Django REST Framework.

This module provides utilities to validate JWTs from Auth0 using python-jose.
"""

import json
import logging
from typing import Dict, Any, Optional
from urllib.request import urlopen

from django.conf import settings
from jose import jwt, JWTError
from jose.exceptions import JWTClaimsError, ExpiredSignatureError

logger = logging.getLogger(__name__)


class Auth0JWTVerifier:
    """
    Utility class for verifying Auth0 JWTs.
    
    This class handles:
    - Fetching Auth0's public keys (JWKS)
    - Verifying JWT signatures
    - Validating JWT claims
    """
    
    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.api_identifier = settings.AUTH0_API_IDENTIFIER
        self.algorithms = [settings.AUTH0_ALGORITHMS]
        self.jwks_url = f"https://{self.domain}/.well-known/jwks.json"
        self._jwks = None
    
    def get_jwks(self) -> Dict[str, Any]:
        """
        Fetch and cache Auth0's JSON Web Key Set (JWKS).
        
        Returns:
            Dict containing the JWKS data
            
        Raises:
            Exception: If unable to fetch JWKS
        """
        if self._jwks is None:
            try:
                with urlopen(self.jwks_url) as response:
                    self._jwks = json.loads(response.read())
                logger.info("Successfully fetched Auth0 JWKS")
            except Exception as e:
                logger.error(f"Failed to fetch Auth0 JWKS: {e}")
                raise Exception(f"Unable to fetch Auth0 JWKS: {e}")
        
        return self._jwks
    
    def get_signing_key(self, token: str) -> str:
        """
        Get the signing key for a JWT token.
        
        Args:
            token: The JWT token
            
        Returns:
            The signing key
            
        Raises:
            Exception: If unable to find the signing key
        """
        try:
            # Decode the header to get the key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            if not kid:
                raise Exception("Token header missing 'kid' claim")
            
            # Get JWKS and find the matching key
            jwks = self.get_jwks()
            
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    # Convert JWK to PEM format
                    from jose.backends import RSAKey
                    return RSAKey(key, algorithm='RS256')
            
            raise Exception(f"Unable to find key with kid: {kid}")
            
        except Exception as e:
            logger.error(f"Failed to get signing key: {e}")
            raise Exception(f"Unable to get signing key: {e}")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode an Auth0 JWT token.
        
        Args:
            token: The JWT token to verify
            
        Returns:
            Dict containing the decoded token payload
            
        Raises:
            JWTError: If token verification fails
            JWTClaimsError: If token claims are invalid
            ExpiredSignatureError: If token has expired
        """
        try:
            # Get the signing key
            signing_key = self.get_signing_key(token)
            
            # Verify and decode the token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=self.algorithms,
                audience=self.api_identifier,
                issuer=f"https://{self.domain}/"
            )
            
            logger.info(f"Successfully verified Auth0 JWT for user: {payload.get('sub')}")
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Auth0 JWT token has expired")
            raise
        except JWTClaimsError as e:
            logger.warning(f"Auth0 JWT claims validation failed: {e}")
            raise
        except JWTError as e:
            logger.error(f"Auth0 JWT verification failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Auth0 JWT verification: {e}")
            raise JWTError(f"Token verification failed: {e}")


def verify_auth0_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to verify an Auth0 JWT token.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        Dict containing the decoded token payload, or None if verification fails
    """
    try:
        verifier = Auth0JWTVerifier()
        return verifier.verify_token(token)
    except Exception as e:
        logger.error(f"Auth0 token verification failed: {e}")
        return None


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract user information from a verified Auth0 JWT token.
    
    Args:
        token: The JWT token
        
    Returns:
        Dict containing user information, or None if token is invalid
    """
    payload = verify_auth0_token(token)
    if not payload:
        return None
    
    return {
        'sub': payload.get('sub'),
        'email': payload.get('email'),
        'given_name': payload.get('given_name'),
        'family_name': payload.get('family_name'),
        'name': payload.get('name'),
        'nickname': payload.get('nickname'),
        'picture': payload.get('picture'),
        'phone_number': payload.get('phone_number'),
        'address': payload.get('address'),
        'aud': payload.get('aud'),
        'iss': payload.get('iss'),
        'exp': payload.get('exp'),
        'iat': payload.get('iat'),
    }
