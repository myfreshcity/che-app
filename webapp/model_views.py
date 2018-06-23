from flask import url_for, request, flash, jsonify
from flask_admin import BaseView, expose
from flask_admin.babel import gettext
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from flask_admin.contrib.sqla.view import log
from flask_admin.form import FormOpts
from flask_admin.helpers import get_redirect_target
from flask_admin.model.helpers import get_mdict_item_or_list
from flask_login import current_user
from flask_security.utils import hash_password
from sqlalchemy import func
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from webapp import db
from webapp.models import User, Car, Order, BasicCar, orders_cars


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


class MyModelViewUser(MyModelView):
    column_labels = dict(
        email=u'账号',
        username=u'公司名称',
        password=u'密码',
    )

    can_create = True
    form_excluded_columns = ['roles','login_count','current_login_ip',
                             'last_login_ip','current_login_at','last_login_at',
                             'confirmed_at','active','openid']

    # column_select_related_list = ['mps',]
    column_formatters = dict(
        password=lambda v, c, m, p: '**' + m.password[-6:],
    )
    column_searchable_list = (User.email,)

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        if current_user.has_role('admin'):
            return True
        return False


    def create_model(self, form):
        """
            Create model from form.

            :param form:
                Form instance
        """
        try:
            model = self.model()
            form.populate_obj(model)
            model.password = hash_password(model.password)
            model.active = 1
            self.session.add(model)

            from webapp.app import user_datastore
            normal_role = user_datastore.find_role('superuser')
            user_datastore.add_role_to_user(model, normal_role)

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

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        """
            Create model view
        """
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_create:
            return redirect(return_url)

        form = self.create_form()
        if not hasattr(form, '_validated_ruleset') or not form._validated_ruleset:
            self._validate_form_instance(ruleset=self._form_create_rules, form=form)

        if self.validate_form(form):
            # in versions 1.1.0 and before, this returns a boolean
            # in later versions, this is the model itself

            model = self.create_model(form)

            if model:
                flash(gettext('Record was successfully created.'), 'success')
                if '_add_another' in request.form:
                    return redirect(request.url)
                elif '_continue_editing' in request.form:
                    # if we have a valid model, try to go to the edit view
                    if model is not True:
                        url = self.get_url('.edit_view', id=self.get_pk_value(model), url=return_url)
                    else:
                        url = return_url
                    return redirect(url)
                else:
                    # save button
                    return redirect(self.get_save_return_url(model, is_created=True))

        form_opts = FormOpts(widget_args=self.form_widget_args,
                             form_rules=self._form_create_rules)

        if self.create_modal and request.args.get('modal'):
            template = self.create_modal_template
        else:
            template = self.create_template

        return self.render(template,
                           form=form,
                           form_opts=form_opts,
                           return_url=return_url)

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        """
            Edit model view
        """
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_edit:
            return redirect(return_url)

        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model is None:
            flash(gettext('Record does not exist.'), 'error')
            return redirect(return_url)

        form = self.edit_form(obj=model)
        delattr(form, 'password')

        if not hasattr(form, '_validated_ruleset') or not form._validated_ruleset:
            self._validate_form_instance(ruleset=self._form_edit_rules, form=form)

        if self.validate_form(form):
            if self.update_model(form, model):
                flash(gettext('Record was successfully saved.'), 'success')
                if '_add_another' in request.form:
                    return redirect(self.get_url('.create_view', url=return_url))
                elif '_continue_editing' in request.form:
                    return redirect(request.url)
                else:
                    # save button
                    return redirect(self.get_save_return_url(model, is_created=False))

        if request.method == 'GET' or form.errors:
            self.on_form_prefill(form, id)

        form_opts = FormOpts(widget_args=self.form_widget_args,
                             form_rules=self._form_edit_rules)

        if self.edit_modal and request.args.get('modal'):
            template = self.edit_modal_template
        else:
            template = self.edit_template

        return self.render('user/edit.html',
                           model=model,
                           form=form,
                           form_opts=form_opts,
                           return_url=return_url)


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
                 if o.t_status > 0:
                     o.pay_amt = car.price
                     query.append(o)
        count = len(query)
        return count, query



class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('index.html')