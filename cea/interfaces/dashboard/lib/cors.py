from typing import List, Optional


class CORSConfig:

    def __init__(
        self,
        origins: List[str],
        allow_credentials: bool,
        methods: List[str],
        headers: List[str]
    ):
        """
        Initialise CORS configuration.

        Args:
            origins: List of allowed origins (e.g., ["http://localhost:5050"]) or ["*"] for wildcard
            allow_credentials: Whether to allow credentials (cookies, auth headers)
            methods: List of allowed HTTP methods
            headers: List of allowed HTTP headers
        """
        self.origins = origins
        self.allow_credentials = allow_credentials
        self.methods = methods
        self.headers = headers

    def get_response_headers(self, request_origin: Optional[str] = None) -> dict:
        """
        Get CORS headers for manual responses (e.g., exception handlers).

        Security: Only returns CORS headers if the request origin is allowed.
        For untrusted origins, returns empty dict (no CORS headers).

        Args:
            request_origin: The Origin header from the request (optional)

        Returns:
            Dictionary of CORS headers to include in response.
            Empty dict if request origin is not in allowed origins.
        """
        headers = {}

        if self.origins == ["*"]:
            # Wildcard mode - allow any origin
            headers["Access-Control-Allow-Origin"] = "*"
        else:
            # Only send CORS headers if request origin is in allowed list
            if request_origin and request_origin in self.origins:
                headers["Access-Control-Allow-Origin"] = request_origin

                if self.allow_credentials:
                    headers["Access-Control-Allow-Credentials"] = "true"
            # else: No CORS headers for untrusted origins (secure default)

        return headers

    @property
    def is_wildcard(self) -> bool:
        """Check if CORS is configured with wildcard origin."""
        return self.origins == ["*"]

    def __repr__(self) -> str:
        return (
            f"CORSConfig(origins={self.origins}, "
            f"allow_credentials={self.allow_credentials}, "
            f"methods={self.methods}, "
            f"headers={self.headers})"
        )
