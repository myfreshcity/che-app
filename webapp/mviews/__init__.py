from flask import url_for, request
from flask_admin.contrib import sqla
from flask_login import current_user
from werkzeug.exceptions import abort
from werkzeug.utils import redirect


class MyModelView(sqla.ModelView):
    can_delete = False
    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))