
from django.http import HttpResponse
from django.shortcuts import render,get_object_or_404
from .models import Product
from Category.models import Category
from cart.models import CartItem
from cart.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
# Create your views here.
def store(request, category_slug=None):
    category=None   
    products=None
    if category_slug != None:
        category=get_object_or_404(Category, slug=category_slug)
        products=Product.objects.filter(category=category, is_available=True)
        paginalor= Paginator(products, 3)
        page=request.GET.get('page')
        paged_products=paginalor.get_page(page)
        product_count=products.count()
    else:
        products=Product.objects.all().filter(is_available=True).order_by('id')
        paginator= Paginator(products, 3)
        page=request.GET.get('page')
        paged_products=paginator.get_page(page)
        product_count=products.count()
    context={
        'products': paged_products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html',context)

def product_detail(request, category_slug, product_slug):
    try:
        product = get_object_or_404(Product, category__slug=category_slug, slug=product_slug)
        in_cart=CartItem.objects.filter(cart__cart_id=_cart_id(request), product=product).exists()
        
    except Exception as e:
        raise e
    
    context = {
        'product': product,
        'in_cart': in_cart,
    }
    return render(request, 'store/product_detail.html', context)

def search(request):
    
    products = Product.objects.none()  # Default to empty queryset
    product_count = 0
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        
        if keyword:
           products = Product.objects.filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword)).order_by('-created_date')
           product_count = products.count()
        else:
            products = Product.objects.all().order_by('-created_date')
            product_count = products.count()
        
    else:
        paged_products = products
    context={
        'products': products,
        'product_count': product_count,
    }
  
    return render(request, 'store/store.html', context)