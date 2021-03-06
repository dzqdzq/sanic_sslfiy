# -*- coding: utf-8 -*-

from sanic.response import redirect


class SSLify():
    """Secures your Sanic App."""

    _instance = None
    _instantiated = False


    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self, app, hsts_age=None, hsts_include_subdomains=None, permanent_redirection=None, paths_to_skip=None):
        if not type(self)._instantiated:
            type(self)._instantiated = True

            self.app = app

            if hsts_age is not None:
                self.app.config['SSLIFY_HSTS_AGE'] = hsts_age
            elif hsts_age is None \
            and 'SSLIFY_HSTS_AGE' not in self.app.config:
                self.app.config['SSLIFY_HSTS_AGE'] = 31536000
            self.hsts_age = self.app.config['SSLIFY_HSTS_AGE']

            if hsts_include_subdomains is not None:
                self.app.config['SSLIFY_HSTS_INCLUDE_SUBDOMAINS'] = hsts_include_subdomains
            elif hsts_include_subdomains is None \
            and 'SSLIFY_HSTS_INCLUDE_SUBDOMAINS' not in self.app.config:
                self.app.config['SSLIFY_HSTS_INCLUDE_SUBDOMAINS'] = False
            self.hsts_include_subdomains = self.app.config['SSLIFY_HSTS_INCLUDE_SUBDOMAINS']

            if permanent_redirection is not None:
                self.app.config['SSLIFY_PERMANENT_REDIRECTION'] = permanent_redirection
            elif permanent_redirection is None \
            and 'SSLIFY_PERMANENT_REDIRECTION' not in self.app.config:
                self.app.config['SSLIFY_PERMANENT_REDIRECTION'] = False
            self.permanent_redirection = self.app.config['SSLIFY_PERMANENT_REDIRECTION']

            if paths_to_skip is not None:
                self.app.config['SSLIFY_PATHS_TO_SKIP'] = paths_to_skip
            elif paths_to_skip is None \
            and 'SSLIFY_PATHS_TO_SKIP' not in self.app.config:
                self.app.config['SSLIFY_PATHS_TO_SKIP'] = []
            self.paths_to_skip = self.app.config['SSLIFY_PATHS_TO_SKIP']

            self.app.register_middleware(self.redirect_to_ssl, attach_to='request')
            self.app.register_middleware(self.set_hsts_header, attach_to='response')


    @property
    def hsts_header(self):
        """Returns the proper HSTS policy."""
        hsts_policy = 'max-age={0}'.format(self.hsts_age)
        if self.hsts_include_subdomains:
            hsts_policy += '; includeSubDomains'
        return hsts_policy


    def path_is_to_skip(self, request):
        """Checks if path is in the skip paths list."""
        return bool(list(filter(lambda path_to_skip: request.path.startswith('/{0}'.format(path_to_skip)), self.paths_to_skip)))


    def redirect_to_ssl(self, request):
        """Redirect incoming requests to HTTPS."""
        # Should we redirect?
        criteria = [
            request.scheme == 'https',
            self.app.debug,
            request.headers.get('X-Forwarded-Proto', 'http') == 'https']

        if not any(criteria) and not self.path_is_to_skip(request):
            if request.url.startswith('http://'):
                url = request.url.replace('http://', 'https://', 1)
                status = 302
                if self.permanent_redirection:
                    status = 301
                return redirect(url, status=status)


    def set_hsts_header(self, request, response):
        """Adds HSTS header to response."""
        if not self.path_is_to_skip(request):
            response.headers.setdefault('Strict-Transport-Security', self.hsts_header)
