from flask import request, flash
from flask_admin import expose
from flask_admin.babel import gettext
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from flask_admin.contrib.sqla.view import log
from flask_login import current_user
from sqlalchemy import func
from werkzeug.exceptions import abort

from webapp import db
from webapp.mviews import MyModelView
from webapp.models import Car, BasicCar


class MyModelViewBrand(MyModelView):
    column_labels = dict(
        initial=u'首字母',
        full_name=u'名称',
    )
    # 如果不想显示某些字段，可以重载这个变量
    column_exclude_list = (
        'img_address',
    )

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        if current_user.has_role('admin'):
            return True
        return False


class MyModelViewBasicCar(MyModelView):
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

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        if current_user.has_role('admin'):
            return True
        return False


class MyModelViewCar(MyModelView):
    column_labels = dict(
        bcar=u'基础车型',
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
        'brand','cat','bcar','user_name'
    )

    form_excluded_columns = [
        'brand','cat','full_name','orders','user_name'
    ]

    loader = QueryAjaxModelLoader('basic_cars', db.session, BasicCar,
                                     fields=['id','full_name'],
                                     page_size=10,
                                     placeholder="Select a car"
                                     )


    form_ajax_refs = {
        'bcar': loader
    }

    @expose('/ajax/lookup/')
    def ajax_lookup(self):
        name = request.args.get('name')
        query = request.args.get('query')
        offset = request.args.get('offset', type=int)
        limit = request.args.get('limit', 10, type=int)

        loader = self.loader

        if not loader:
            abort(404)

        data = [loader.format(m) for m in loader.get_list(query, offset, limit)]
        from flask import Response
        import json
        return Response(json.dumps(data), mimetype='application/json')

    def get_query(self):
        return self.session.query(self.model).filter(Car.user_id == current_user.id)

    def get_count_query(self):
        return self.session.query(func.count('*')).select_from(self.model).filter(Car.user_id == current_user.id)

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            model.user_id = current_user.id
            model.user_name = current_user.username

            model.full_name = form.data['bcar'].full_name
            model.cat_id = form.data['bcar'].cat_id
            model.brand_id = form.data['bcar'].brand_id
            model.guid_price = form.data['bcar'].guid_price
            self.session.add(model)

            self._on_model_change(form, model, True)
            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to create record. %(error)s', error=str(ex)), 'error')
                log.exception('Failed to create record.')

            self.session.rollback()

            return False
        else:
            self.after_model_change(form, model, True)

        return model


    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        if current_user.has_role('superuser'):
            return True
        return False