from operator import is_, le
from django.http import HttpResponse
from accounts.models import Account
from django.shortcuts import redirect, render, get_object_or_404
from .models import Cart, CartItem
from store.models import Product,Variation
from django.contrib.auth.decorators import login_required
import requests
# Create your views here.
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart
def cart(request):
    return render(request, 'store/cart.html')    

def add_cart(request, id):
    current_user=request.user
    product = Product.objects.get(id=id)
    # If user is authenticated, add the product to the cart for that user
    if current_user.is_authenticated:
        
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass

        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        if is_cart_item_exists:
            cart_items = CartItem.objects.filter(product=product, user=current_user)
            ex_var_list = []
            id_list = []
            for item in cart_items:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id_list.append(item.id)

            if product_variation in ex_var_list:
                # Increase quantity for the matching variation
                index = ex_var_list.index(product_variation)
                item_id = id_list[index]
                item = CartItem.objects.get(id=item_id)
                item.quantity += 1
                item.save()
            else:
                # Create new cart item with new variation
                cart_item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    user=current_user,
                )
                if len(product_variation) > 0:
                    cart_item.variations.set(product_variation)
                cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user,
            )
            if len(product_variation) > 0:
                cart_item.variations.set(product_variation)
            cart_item.save()
        return redirect('cart')
    
    else:
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass

        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
            cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exists:
            cart_items = CartItem.objects.filter(product=product, cart=cart)
            ex_var_list = []
            id_list = []
            for item in cart_items:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id_list.append(item.id)

            if product_variation in ex_var_list:
                # Increase quantity for the matching variation
                index = ex_var_list.index(product_variation)
                item_id = id_list[index]
                item = CartItem.objects.get(id=item_id)
                item.quantity += 1
                item.save()
            else:
                # Create new cart item with new variation
                cart_item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    cart=cart,
                )
                if len(product_variation) > 0:
                    cart_item.variations.set(product_variation)
                cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )
            if len(product_variation) > 0:
                cart_item.variations.set(product_variation)
            cart_item.save()
        return redirect('cart')

def cart(request, total=0,quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart=Cart.objects.get(cart_id=_cart_id(request))
            cart_items=CartItem.objects.filter(cart=cart, is_active=True)
            
            # Calculate totals
            for cart_item in cart_items:
                total += (cart_item.product.price * cart_item.quantity)
                quantity += cart_item.quantity

            tax= (total * 0.2)
            grand_total= total + tax
    except Cart.DoesNotExist:
        pass

   

    context={
       'total':total,
       'quantity':quantity,
       'cart_items':cart_items,
       'tax':tax,
        'grand_total':grand_total,
    }
    return render(request, 'store/cart.html', context)
    
def remove_cart(request, id,cart_item_id):
    
    product=get_object_or_404(Product, id=id)
    try:
        if request.user.is_authenticated:
            cart_item=CartItem.objects.get(product=product, user=request.user,id=cart_item_id)
        else:
            cart=Cart.objects.get(cart_id=_cart_id(request))
            cart_item=CartItem.objects.get(product=product, cart=cart,id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

def remove_cart_item(request, id,cart_item_id):
  
    product=get_object_or_404(Product, id=id)
    if request.user.is_authenticated:
        cart_item=CartItem.objects.get(product=product, user=request.user,id=cart_item_id)
    else:
        cart=Cart.objects.get(cart_id=_cart_id(request))
        cart_item=CartItem.objects.get(product=product, cart=cart,id=cart_item_id)
    cart_item.delete()
    return redirect('cart')


@login_required(login_url='login')
def checkout(request,total=0,quantity=0, cart_items=None):
    
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart=Cart.objects.get(cart_id=_cart_id(request))
            cart_items=CartItem.objects.filter(cart=cart, is_active=True)
        
        # Calculate totals
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        tax= (total * 0.2)
        grand_total= total + tax

    except Cart.DoesNotExist:
        pass
   

    context={
       'total':total,
       'quantity':quantity,
       'cart_items':cart_items,
       'tax':tax,
       'grand_total':grand_total,
    }
    return render(request, 'store/checkout.html',context)