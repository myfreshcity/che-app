from flask_login import current_user

from webapp.mviews import MyModelView
from webapp.models import Order, Car


class MyModelViewOrder(MyModelView):
    form_create_rules = ('pay_amt', 'contact_way', 'created_time')

    can_view_details = True
    can_create = False
    can_edit = False

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

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        if current_user.has_role('superuser'):
            return True
        return False

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True, page_size=None):
        query = []
        cars = self.session.query(Car).filter(Car.user_id == current_user.id).all()
        for car in cars:
            if car.orders:
                for o in car.orders:
                 if o.t_status > 10:
                     o.pay_amt = car.price
                     query.append(o)
        count = len(query)
        return count, query