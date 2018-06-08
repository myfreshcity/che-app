import json

from webapp import db
from webapp.models import Brand, Car, Category
from webapp.utils import new_alchemy_encoder


def get_brands():
    list = db.session.query(Car, Category, Brand).filter(
        Brand.id == Car.brand_id, Category.id == Car.cat_id, Car.is_show == 1).all()

    brands = set()
    for (car, cat, brand) in list:
        # 设置车辆列表
        c = car
        c.img_url = cat.img_url

        # 设置品牌列表
        b = brand
        for br in brands:
            if b == br:
                b = br
                break
        if not hasattr(b, 'cats'):
            b.cats = set()
        else:
            for bc in b.cats:
                if bc == cat:
                    cat = bc
        if not hasattr(cat, 'cars'):
            cat.cars = []
        cat.cars.append(c)
        b.cats.add(cat)
        brands.add(b)

    result = []
    for it in brands:
        l = []
        for il in it.cats:
            ob = il.to_json()
            ob['cars'] = json.dumps(il.cars, cls=new_alchemy_encoder(), check_circular=False)
            l.append(ob)
        i = {'title': it.full_name, 'list': l}
        result.append(i)
    return {'status': 200, 'message': '', 'aside': result}

def get_car_detail(id):
    car = db.session.query(Car).filter(Car.id == id).first()
    result = {}
    result['view'] = car.to_json()
    result['swiper'] = [{
        'id':1,
        'imgSrc':result['view']['img_url']
    }]
    result['view']['chose'] = [{
        'col': '黑',
        'size':'2016款'
    }]
    return {'status': 200, 'message': '', 'car': result}

def get_index():
    result = {}
    result['swiper'] = [
        {
        'id': 1,
        'imgPath': 'http://localhost:8000/imgs'+'/home/banner_1.jpg'
        },
        {
            'id': 2,
            'imgPath': 'http://localhost:8000/imgs'+'/home/banner_2.jpg'

        }]

    section1 = {
        'list':[
        {
            'id': 32040,
            'imgPath': 'http://localhost:8000/imgs' + '/home/400×400.jpg'
        },
        {
            'id': 32041,
            'imgPath': 'http://localhost:8000/imgs' + '/home/400×400_2.jpg'
        }],
        'banner':'http://localhost:8000/imgs'+'/home/400×100_1.jpg'
    }

    result['section1'] = section1

    return {'status': 200, 'message': '', 'result': result}
