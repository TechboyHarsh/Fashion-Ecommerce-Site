from django.shortcuts import render,redirect
from . models import Contact,User,Product,Wishlist,Cart,Transaction
from django.conf import settings
from django.core.mail import send_mail
import random
from .paytm import generate_checksum, verify_checksum
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

def initiate_payment(request):
    try:
        user=User.objects.get(email=request.session['email'])
        amount = int(request.POST['amount'])
    except:
        return render(request, 'mycart.html', context={'error': 'Wrong Accound Details or amount'})

    transaction = Transaction.objects.create(made_by=user, amount=amount)
    transaction.save()
    merchant_key = settings.PAYTM_SECRET_KEY

    params = (
        ('MID', settings.PAYTM_MERCHANT_ID),
        ('ORDER_ID', str(transaction.order_id)),
        ('CUST_ID', str(transaction.made_by.email)),
        ('TXN_AMOUNT', str(transaction.amount)),
        ('CHANNEL_ID', settings.PAYTM_CHANNEL_ID),
        ('WEBSITE', settings.PAYTM_WEBSITE),
        # ('EMAIL', request.user.email),
        # ('MOBILE_N0', '9911223388'),
        ('INDUSTRY_TYPE_ID', settings.PAYTM_INDUSTRY_TYPE_ID),
        ('CALLBACK_URL', 'http://127.0.0.1:8000/callback/'),
        # ('PAYMENT_MODE_ONLY', 'NO'),
    )

    paytm_params = dict(params)
    checksum = generate_checksum(paytm_params, merchant_key)

    transaction.checksum = checksum
    transaction.save()

    paytm_params['CHECKSUMHASH'] = checksum
    print('SENT: ', checksum)
    return render(request, 'redirect.html', context=paytm_params)

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        received_data = dict(request.POST)
        paytm_params = {}
        paytm_checksum = received_data['CHECKSUMHASH'][0]
        for key, value in received_data.items():
            if key == 'CHECKSUMHASH':
                paytm_checksum = value[0]
            else:
                paytm_params[key] = str(value[0])
        # Verify checksum
        is_valid_checksum = verify_checksum(paytm_params, settings.PAYTM_SECRET_KEY, str(paytm_checksum))
        if is_valid_checksum:
            received_data['message'] = "Checksum Matched"
        else:
            received_data['message'] = "Checksum Mismatched"
            return render(request, 'callback.html', context=received_data)
        return render(request, 'callback.html', context=received_data)


def index(request):
    return render(request, 'index.html')
def seller_index(request):
    return render(request, 'seller_index.html')
def seller_home(request):
    return render(request, 'seller_index.html')
def about(request):
    return render(request, 'about.html')
def blog(request):
    return render(request, 'blog.html')
def register(request):
    if request.method == "POST":
        try:
            user = User.objects.get(email=request.POST['email'])
            msg = "Email Already Exist"
            return render(request,'register.html',{'msg':msg})
        except :
            if request.POST['password'] == request.POST['cpassword']:
                User.objects.create(
                    fname=request.POST['fname'],
                    lname=request.POST['lname'],
                    email=request.POST['email'],
                    mobile=request.POST['mobile'],
                    address=request.POST['address'],
                    gender=request.POST['gender'],
                    password=request.POST['password'],
                    cpassword=request.POST['cpassword'],
                    image=request.FILES['image'],
                    usertype=request.POST['usertype']
                )
                subject = 'OTP For Registration'
                otp=random.randint(1000,9999)
                message = 'Hello User, Your OTP For Successfull Registration is : ' + str(otp)
                email_from = settings.EMAIL_HOST_USER 
                recipient_list = [request.POST['email'],] 
                send_mail(subject, message, email_from, recipient_list)

                return render(request,'otp.html',{'otp':otp,'email':request.POST['email']})
            else:
                msg = "Password And Confirm Does Not Match"
                return render(request,'register.html',{'msg':msg})    
    else:
        return render(request, 'register.html')
def login(request):
    if request.method == "POST":
        if request.POST['action'] == "Forget Password":
            return render(request, "enter_email.html")
        elif request.POST['action'] == "Login":
            try:
                user = User.objects.get(
                    email=request.POST['email'],
                    password=request.POST['password']
                )
                if user.usertype=="user":
                    wishlists=Wishlist.objects.filter(user=user)
                    carts=Cart.objects.filter(user=user)
                    request.session['fname']=user.fname
                    request.session['email'] = user.email
                    request.session['image']=user.image.url
                    request.session['wishlist_count']=len(wishlists)
                    request.session['cart_count']=len(carts)
                    return render(request,'index.html')
                elif user.usertype=="seller":
                    request.session['fname']=user.fname
                    request.session['email'] = user.email
                    request.session['image']=user.image.url
                    return render(request,'seller_index.html')
            except:
                msg = "Email Or Password Is Incorrect"
                return render(request, 'login.html', {'msg': msg})
    else:
        return render(request, 'login.html')
def contact(request):
    if request.method == "POST":
        try:
            contact = Contact.objects.get(email=request.POST['email'])
            msg = "Email Already Exist"
            contacts = Contact.objects.all().order_by('-id')[:5]
            return render(request,'contact.html',{'msg':msg,'contacts':contacts})
        except:
            Contact.objects.create(
                name=request.POST['name'],
                email=request.POST['email'],
                mobile=request.POST['mobile'],
                remarks=request.POST['remarks'],
            )
            contacts=Contact.objects.all().order_by('-id')[:5]
            msg="Contact Saved Sucessfully"
            return render(request, 'contact.html',{'msg':msg,'contacts':contacts})
    else:
        contacts = Contact.objects.all().order_by('-id')[:5]
        return render(request,'contact.html',{'contacts':contacts})
    
def enter_otp(request):
    otp1 = request.POST['otp1']
    otp2 = request.POST['otp2']
    email1 = request.POST['email']

    if otp1 == otp2:
        user = User.objects.get(email=email1)
        user.status="active"
        user.save()
        msg="User Verified Succesfully"
        return render(request, 'login.html', {'msg': msg})
    else:
        msg = "Invalid OTP"
        return render(request, 'otp.html', {'otp': otp1,'email':email1,'msg':msg})
    
def enter_email(request):
    if request.method == "POST":
        try:
            user = User.objects.get(email=request.POST['email'])
            subject = 'OTP For Forgot Password'
            otp=random.randint(1000,9999)
            message = 'Hello User, Your OTP For Forgot Password is : ' + str(otp)
            email_from = settings.EMAIL_HOST_USER 
            recipient_list = [request.POST['email'],] 
            send_mail(subject, message, email_from, recipient_list)
            return render(request,'forget_enter_otp.html',{'otp':otp ,'email':request.POST['email'] })

        except :
            msg = "Email Does Not Exists In The System"
            return render(request, 'enter_email.html', {'msg': msg})      

def verify_forgot_otp(request):
    if request.method == "POST":
        otp1 = request.POST['otp1']
        otp2 = request.POST['otp2']
        email = request.POST['email']

        if otp1 == otp2:
            return render(request,'new_password.html',{'email':email})
        else:
            msg = "Entered OTP Is Invalid"
            return render(request,'forget_enter_otp.html',{'otp':otp1,'msg':msg,'email':email})
            
def update_password(request):
    if request.method == "POST":
        user=User.objects.get(email=request.POST['email'])

        if request.POST['npassword']==request.POST['cnpassword']:
            user.password=request.POST['npassword']
            user.cpassword=request.POST['npassword']
            user.save()
            return render(request,'login.html')
        else:
            msg="New Password And Confirm New Password Does Not Matched"
            return render(request, 'new_password.html', {'email': request.POST['email'], 'msg': msg})

def logout(request):
    try:
        del request.session['email']
        del request.session['fname']
        del request.session['image']
        return render(request, 'login.html')
    except:
        pass


def change_password(request):
    if request.method == "POST":
        user = User.objects.get(email=request.session['email'])

        if user.password == request.POST['old_password']:
            if request.POST['npassword'] == request.POST['cnpassword']:
                user.password = request.POST['npassword']
                user.cpassword = request.POST['npassword']
                user.save()
                return redirect('logout')
            else:
                msg = "New Password And Confirm New Password Does Not Matched"
                return render(request, 'change_password.html',{'msg':msg})
        else:
            msg = "Old Password Is Incorrect"
            return render(request, 'change_password.html',{'msg':msg})
    else:
        return render(request, 'change_password.html')

def seller_change_password(request):
    if request.method == "POST":
        user = User.objects.get(email=request.session['email'])

        if user.password == request.POST['old_password']:
            if request.POST['npassword'] == request.POST['cnpassword']:
                user.password = request.POST['npassword']
                user.cpassword = request.POST['npassword']
                user.save()
                return redirect('logout')
            else:
                msg = "New Password And Confirm New Password Does Not Matched"
                return render(request, 'seller_change_password.html',{'msg':msg})
        else:
            msg = "Old Password Is Incorrect"
            return render(request, 'seller_change_password.html',{'msg':msg})
    else:
        return render(request, 'seller_change_password.html')

def edit_profile(request):
    user=User.objects.get(email=request.session['email'])
    if request.method == "POST":

        user.fname=request.POST['fname']
        user.lname=request.POST['lname']
        user.mobile=request.POST['mobile']
        user.email=request.POST['email']
        user.address=request.POST['address']
        user.gender=request.POST['gender']
        try:
            user.image=request.FILES['image']
            user.save()
            user=User.objects.get(email=request.session['email'])
            msg="Profile Saved Successfully"
            request.session['image']=user.image.url
            request.session['fname']=user.fname
            return render(request,'edit_profile.html',{'user':user,'msg':msg})
        except:
            user.save()
            user=User.objects.get(email=request.session['email'])
            msg="Profile Saved Successfully"
            request.session['fname']=user.fname
            return render(request,'edit_profile.html',{'user':user,'msg':msg})

    else:
        return render(request,'edit_profile.html',{'user':user})

def seller_edit_profile(request):
    user=User.objects.get(email=request.session['email'])
    if request.method == "POST":

        user.fname=request.POST['fname']
        user.lname=request.POST['lname']
        user.mobile=request.POST['mobile']
        user.email=request.POST['email']
        user.address=request.POST['address']
        user.gender=request.POST['gender']
        try:
            user.image=request.FILES['image']
            user.save()
            user=User.objects.get(email=request.session['email'])
            msg="Profile Saved Successfully"
            request.session['image']=user.image.url
            request.session['fname']=user.fname
            return render(request,'seller_edit_profile.html',{'user':user,'msg':msg})
        except:
            user.save()
            user=User.objects.get(email=request.session['email'])
            msg="Profile Saved Successfully"
            request.session['fname']=user.fname
            return render(request,'seller_edit_profile.html',{'user':user,'msg':msg})

    else:
        return render(request,'seller_edit_profile.html',{'user':user})

def seller_add_product(request):
    if request.method=="POST":
        seller=User.objects.get(email=request.session['email'])
        Product.objects.create(
            seller=seller,
            product_brand=request.POST['product_brand'],
            product_model=request.POST['product_model'],
            product_price=request.POST['product_price'],
            product_desc=request.POST['product_desc'],
            product_image=request.FILES['product_image'],
        )
        msg="Product Added Successfully"
        return render(request,'seller_add_product.html',{'msg':msg})
    else:
         return render(request,'seller_add_product.html')

def seller_view_product(request):
    seller=User.objects.get(email=request.session['email'])
    products=Product.objects.filter(seller=seller)
    return render(request,'seller_view_product.html',{'products':products})

def seller_product_detail(request,pk):
    product=Product.objects.get(pk=pk)
    return render(request,'seller_product_detail.html',{'product':product})

def seller_edit_product(request,pk):
    product=Product.objects.get(pk=pk)
    if request.method=="POST":
        product.product_model=request.POST['product_model']
        product.product_price=request.POST['product_price']
        product.product_desc=request.POST['product_desc']
        try:
            product.product_image=request.FILES['product_image']
            product.save()
            return redirect('seller_view_product')
        except:
            product.save()
            return redirect('seller_view_product')
    else:
        return render(request,'seller_edit_product.html',{'product':product})

def seller_delete_product(request,pk):
    product=Product.objects.get(pk=pk)
    product.delete()
    return redirect('seller_view_product')

def user_view_product(request,pb):
    if pb=="All":
        products=Product.objects.all()
        return render(request,'user_view_product.html',{'products':products})
    else:
        products=Product.objects.filter(product_brand=pb)
        return render(request,'user_view_product.html',{'products':products})

def user_product_detail(request,pid):
    flag=False
    flag1=False
    product=Product.objects.get(pk=pid)
    try:
        user=User.objects.get(email=request.session['email'])
        try:
            Wishlist.objects.get(user=user,product=product)
            flag=True
        except:
            pass
        try:
            Cart.objects.get(user=user,product=product)
            flag1=True
        except:
            pass    
        return render(request,'user_product_detail.html',{'product':product,'flag':flag,'flag1':flag1})
    except:
        return render(request,'only_product_detail.html',{'product':product})

def mywishlist(request):
    user=User.objects.get(email=request.session['email'])
    wishlists=Wishlist.objects.filter(user=user)
    request.session['wishlist_count']=len(wishlists)
    return render(request,'mywishlist.html',{'wishlists':wishlists})

def add_to_wishlist(request,pk):
    product=Product.objects.get(pk=pk)
    user=User.objects.get(email=request.session['email'])
    Wishlist.objects.create(user=user,product=product)
    return redirect('mywishlist')

def remove_from_wishlist(request,pk):
    user=User.objects.get(email=request.session['email'])
    product=Product.objects.get(pk=pk)
    wishlist=Wishlist.objects.get(user=user,product=product)
    wishlist.delete()
    return redirect('mywishlist')

def mycart(request):
    net_price=0
    user=User.objects.get(email=request.session['email'])
    carts=Cart.objects.filter(user=user)
    
    for i in carts:
        net_price=net_price+int(i.total_price)

    request.session['cart_count']=len(carts)
    return render(request,'mycart.html',{'carts':carts,'net_price':net_price})

def add_to_cart(request,pk):
    user=User.objects.get(email=request.session['email'])
    product=Product.objects.get(pk=pk) 
    Cart.objects.create(
        user=user,
        product=product,
        price=product.product_price,
        total_price=product.product_price,  
    )
    return redirect('mycart') 

def remove_from_cart(request,pk):
    user=User.objects.get(email=request.session['email'])
    product=Product.objects.get(pk=pk) 
    cart=Cart.objects.get(user=user,product=product)
    cart.delete()
    return redirect('mycart')

def change_qty(request):
    cart=Cart.objects.get(pk=request.POST['pk'])
    qty=request.POST['qty']
    cart.qty=qty
    cart.total_price=int(qty)*int(cart.price)
    cart.save()
    return redirect('mycart')
    