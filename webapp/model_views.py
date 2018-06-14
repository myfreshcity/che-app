from flask import url_for, request
from flask_admin.contrib import sqla
from flask_login import current_user
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from webapp.models import User, Car, Order


class MyModelView(sqla.ModelView):
    can_delete = False

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

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


class MyModelViewUser(MyModelView):
    can_create = False
    # column_select_related_list = ['mps',]
    column_formatters = dict(
        password=lambda v, c, m, p: '**' + m.password[-6:],
    )
    column_searchable_list = (User.email,)


class MyModelViewBrand(MyModelView):
    column_labels = dict(
        initial=u'首字母',
        full_name=u'名称',
    )
    # 如果不想显示某些字段，可以重载这个变量
    column_exclude_list = (
        'img_address',
    )


class MyModelViewCar(MyModelView):
    column_labels = dict(
        is_show=u'是否上架',
        full_name=u'名称',
        guid_price=u'指导价',
        price=u'定金',
        offset_price=u'降价',
        location=u'车源所在地',
        remark=u'备注',
    )
    column_searchable_list = (Car.full_name,)

    column_exclude_list = (
        'brand','cat'
    )


class MyModelViewOrder(MyModelView):
    form_create_rules = ('pay_amt', 'contact_way', 'created_time')

    #can_view_details = True
    can_create = False
    #can_edit = False

    column_labels = dict(
        pay_amt=u'付款金额',
        pay_person_type=u'是否个人',
        contact_way=u'联系方式',
        contact_person=u'联系人',
        remark=u'备注',
        created_time=u'创建时间'
    )

    column_searchable_list = (Order.contact_way,)

    column_exclude_list = (
        'open_id','pay_confirm_time','t_status'
    )

