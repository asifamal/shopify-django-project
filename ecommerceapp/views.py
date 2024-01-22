from django.shortcuts import render,redirect
from ecommerceapp.models import Contact,Product,Orders,OrderUpdate
from django.contrib import messages
from math import ceil
from ecommerceapp.models import Contact, Product, OrderUpdate, Orders
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .keys import RazorpayKeys
import razorpay
from django.shortcuts import render
from .models import Orders, OrderUpdate




def index(request):
    allProds = []
    catprods = Product.objects.values('category','id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category = cat)
        n=len(prod)
        nSlides = n // 4 + ceil(n / 4) - (n // 4)
        allProds.append([prod, range(1, nSlides), nSlides])
    
    params = {'allProds':allProds}


    return render(request,"index.html",params)

def contact(request):
    if request.method=="POST":
        name=request.POST.get("name")
        email=request.POST.get("email")
        desc=request.POST.get("desc")
        pnumber=request.POST.get("pnumber")
        myquery=Contact(name=name,email=email,desc=desc,phonenumber=pnumber)
        myquery.save()
        messages.info(request,"We will get back to you soon...")
    return render(request,"contact.html")


def about(request):
    return render(request,"about.html")


def checkout(request):
    if not request.user.is_authenticated:
        messages.warning(request,"Login & Try Again")
        return redirect('/auth/login')

    if request.method=="POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amt')
        email = request.POST.get('email', '')
        address1 = request.POST.get('address1', '')
        address2 = request.POST.get('address2','')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        Order = Orders(items_json=items_json,name=name,amount=amount, email=email, address1=address1,address2=address2,city=city,state=state,zip_code=zip_code,phone=phone)
        print(amount)
        Order.save()
        update = OrderUpdate(order_id=Order.order_id,update_desc="the order has been placed")
        update.save()
        thank = True

        
        razorpay_client = razorpay.Client(auth=(RazorpayKeys.RAZORPAY_KEY_ID, RazorpayKeys.RAZORPAY_KEY_SECRET))

        
        order_amount = int(amount) * 100  
        order_currency = 'INR'  
        order_receipt = f"{Order.order_id}Shopify"
        razorpay_order = razorpay_client.order.create({'amount': order_amount, 'currency': order_currency, 'receipt': order_receipt})

        order_id = razorpay_order['id']

        return render(request, 'razorpay.html', {'order_id': order_id, 'amount': order_amount, 'razorpay_key_id': RazorpayKeys.RAZORPAY_KEY_ID, 'order': Order, 'payment_id': razorpay_order['id']})



    return render(request, 'checkout.html')
        

def handlerequest(request,payment_id):
    if request.method == 'POST':
        pass
    return render(request, 'razorpay-success.html') 

   
    

def profile(request):
    if not request.user.is_authenticated:
        return redirect('/auth/login')

    user_orders = Orders.objects.filter(email=request.user.email)
    
    order_updates_dict = {}
    for order_update in OrderUpdate.objects.filter(order_id__in=user_orders.values_list('order_id', flat=True)):
        if order_update.order_id not in order_updates_dict or order_update.timestamp > order_updates_dict[order_update.order_id].timestamp:
            order_updates_dict[order_update.order_id] = order_update
    
    order_details = []
    for order in user_orders:
        latest_update = order_updates_dict.get(order.order_id)
        order_details.append({
            'order': order,
            'latest_update': latest_update.update_desc if latest_update else "Order placed",
        })

    context = {
        'order_details': order_details,
    }

    return render(request, "profile.html", context)
