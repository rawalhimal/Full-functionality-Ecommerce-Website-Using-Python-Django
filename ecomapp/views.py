from django.shortcuts import render,redirect
from django.views.generic import TemplateView,View,CreateView,FormView,DetailView,ListView
from .forms import CheckoutForm,CustomerRegistrationForm,CustomerLoginForm
from django.contrib.auth import authenticate,login,logout
from django.db.models import Q
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from .models import *
# Create your views here.

class EcomMixin(object):
    def dispatch(self,request,*args,**kwargs):
        cart_id=self.request.session.get('cart_id')
        if cart_id:
            cart_obj=Cart.objects.get(id=cart_id)
            if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
                cart_obj.customer=request.user.customer
                cart_obj.save()
        return super().dispatch(request,*args,**kwargs)


class HomeView(EcomMixin,TemplateView):
    template_name='home.html'
    
    def get_context_data(self,**kwargs):
        context=super().get_context_data(**kwargs)
        all_products=Product.objects.all().order_by("-id")
        paginator = Paginator(all_products, 3)#show 3 itmes per page
        page_number = self.request.GET.get('page')
        product_list = paginator.get_page(page_number)
        context['product_list']=product_list
        return context

class AllProducts(EcomMixin,TemplateView):
    template_name='allproducts.html'

    def get_context_data(self,**kwargs):
        context=super().get_context_data(**kwargs)
        context['allproducts']=Category.objects.all()
        return context

class ProductDetailView(EcomMixin,TemplateView):
    template_name='productdetail.html'
    def get_context_data(self,**kwargs):
        context=super().get_context_data(**kwargs)
        url_slug=self.kwargs['slug']
        product=Product.objects.get(slug=url_slug)
        product.var_count +=1
        product.save()
        context['product']=product
        return context

class AddToCartView(EcomMixin,TemplateView):
    template_name='addtocart.html'

    def get_context_data(self,**kwargs):
        context=super().get_context_data(**kwargs)
        #get product id from url
        product_id=self.kwargs['pro_id']
        #get product of that id
        product_obj=Product.objects.get(id=product_id)
        #check cart
        cart_id=self.request.session.get('cart_id',None)
        if cart_id :
            cart_obj=Cart.objects.get(id=cart_id)
            this_product_in_cart=cart_obj.cartproduct_set.filter(product=product_obj)

            #items alrealy exist in cart
            if this_product_in_cart.exists():
                cartproduct=this_product_in_cart.last()
                cartproduct.quantity += 1
                cartproduct.subtotal +=product_obj.selling_price
                cartproduct.save()
                cart_obj.total += product_obj.selling_price
                cart_obj.save()

            #new item is added in cart
            else:
                cartproduct = CartProduct.objects.create(cart=cart_obj,product=product_obj,rate=product_obj.selling_price,quantity=1,subtotal=product_obj.selling_price)
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
                
        else:
            cart_obj=Cart.objects.create(total=0)
            self.request.session['cart_id']=cart_obj.id
            cartproduct = CartProduct.objects.create(cart=cart_obj,product=product_obj,rate=product_obj.selling_price,quantity=1,subtotal=product_obj.selling_price)
            cart_obj.total += product_obj.selling_price
            cart_obj.save()

        return context
        #check if product already exists in cart

class AddMyCartView(EcomMixin,TemplateView):
    template_name='mycart.html'
    def get_context_data(self,**kwargs):
        context=super().get_context_data(**kwargs)
        cart_id=self.request.session.get('cart_id',None)
        if cart_id:
            cart=Cart.objects.get(id=cart_id)
        else:
            cart=None
        context['cart']=cart
        return context

class ManageCartView(EcomMixin,View):
    def get(self,request,*args,**kwargs):
        cp_id=self.kwargs['cp_id']
        action=request.GET.get('action')
        cp_obj=CartProduct.objects.get(id=cp_id)
        cart_obj=cp_obj.cart
        if action =='inc':
            cp_obj.quantity += 1
            cp_obj.subtotal += cp_obj.rate
            cp_obj.save()
            cart_obj.total += cp_obj.rate
            cart_obj.save()
        elif action =='dcr':
            cp_obj.quantity -= 1
            cp_obj.subtotal -= cp_obj.rate
            cp_obj.save()
            cart_obj.total -= cp_obj.rate
            cart_obj.save()
            if cp_obj.quantity == 0:
                cp_obj.delete()
        elif action == 'rmv':
            cart_obj.total -= cp_obj.subtotal
            cart_obj.save()
            cp_obj.delete()
        return redirect('ecomapp:mycart')

class EmptyCartView(EcomMixin,View):
    def get(self,request,*args,**kwargs):
        cart_id=request.session.get('cart_id',None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
            cart.cartproduct_set.all().delete()
            cart.total = 0
            cart.save()
        return redirect('ecomapp:mycart')

class CheckoutView(EcomMixin,CreateView):
    template_name='checkout.html'
    form_class=CheckoutForm
    success_url=reverse_lazy('ecomapp:home')

    def dispatch(self,request,*args,**kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            pass 
        else:
            return redirect('/login/?next=/checkout/')
        return super().dispatch(request,*args,**kwargs)

    def get_context_data(self,**kwargs):
        context=super().get_context_data(**kwargs)
        cart_id=self.request.session.get('cart_id',None)
        if cart_id:
            cart_obj=Cart.objects.get(id=cart_id)
        else:
            cart_obj=None
        context['cart']=cart_obj
        return context
    def form_valid(self,form):
        cart_id=self.request.session.get('cart_id')
        if cart_id:
            cart_obj=Cart.objects.get(id=cart_id)
            form.instance.cart=cart_obj
            form.instance.subtotal =cart_obj.total
            form.instance.discount = 0
            form.instance.total=cart_obj.total
            form.instance.order_status="Order Received"
            del self.request.session['cart_id']
        else:
            return redirect('ecompapp:home')
        return super().form_valid(form)

class CustomerRegistration(CreateView):
    template_name='customerregistration.html'
    form_class=CustomerRegistrationForm
    success_url=reverse_lazy('ecomapp:home')
    def form_valid(self,form):
        username=form.cleaned_data.get('username')
        password=form.cleaned_data.get('password')
        email=form.cleaned_data.get('email')
        user=User.objects.create_user(username,email,password)
        form.instance.user = user
        login(self.request,user)
        return super().form_valid(form)
    
    def get_success_url(self):
        if 'next' in self.request.GET:
            next_url=self.request.GET.get('next')
            return next_url
        else:
            return self.success_url

class CustomerLogoutView(View):
    def get(self,request):
        logout(self.request)
        return redirect('ecomapp:home')

class CustomerLoginView(FormView):
    template_name='customerloginform.html'
    form_class=CustomerLoginForm
    success_url=reverse_lazy('ecomapp:home')
    #form valid is the type of post request which is availabe in create view form view and update view
    def form_valid(self,form):
        uname=form.cleaned_data.get('username')
        pword=form.cleaned_data.get('password')
        usr=authenticate(username=uname,password=pword)
        if usr is not None and Customer.objects.filter(user=usr).exists():
            login(self.request,usr)
        else:
            return render(self.request,self.template_name,{'form':self.form_class,'error':'invalid credentials'})
        return super().form_valid(form)
    
    def get_success_url(self):
        if 'next' in self.request.GET:
            next_url=self.request.GET.get('next')
            return next_url
        else:
            return self.success_url
    
class AboutView(EcomMixin,TemplateView):
    template_name='about.html'

class ContactView(EcomMixin,TemplateView):
    template_name='contact.html'


class CustomerDetailView(TemplateView):
    template_name='customerprofile.html'

    def dispatch(self,request,*args,**kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            pass 
        else:
            return redirect('/login/?next=/profile/')
        return super().dispatch(request,*args,**kwargs)

    def get_context_data(self,**kwargs):
        context=super().get_context_data(**kwargs)
        customer=self.request.user.customer
        context['customer']=customer
        order=Order.objects.filter(cart__customer=customer).order_by('-id')
        context['orders']=order
        return context

class CustomerOrderDetailView(DetailView):
    template_name='customerorderdetail.html'
    model=Order
    context_object_name='ord_obj'
    def dispatch(self,request,*args,**kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            order_id=self.kwargs['pk']
            order=Order.objects.get(id=order_id)
            if request.user.customer != order.cart.customer:
                return redirect('/profile/')

        else:
            return redirect('/login/?next=/profile/')
        return super().dispatch(request,*args,**kwargs)

class SearchView(TemplateView):
    template_name='search.html'
    def get_context_data(self,**kwargs):
        context=super().get_context_data(**kwargs)
        kw=self.request.GET.get('keyword')
        results=Product.objects.filter(Q(title__icontains=kw) | Q(description__icontains=kw))
        print(results,'..........')
        context['results']=results
        return context

    #admin pages
class AdminLoginView(FormView):
    template_name='adminpages/adminlogin.html'
    form_class=CustomerLoginForm
    success_url=reverse_lazy('ecomapp:adminhome')
    def form_valid(self,form):
        uname=form.cleaned_data.get('username')
        pword=form.cleaned_data.get('password')
        usr=authenticate(username=uname,password=pword)
        if usr is not None and Admin.objects.filter(user=usr).exists():
            login(self.request,usr)
        else:
            return render(self.request,self.template_name,{'form':self.form_class,'error':'invalid credentials'})
        return super().form_valid(form)

class AdminRequiredMixin(object):
    def dispatch(self,request,*args,**kwargs):
        
        if request.user.is_authenticated and Admin.objects.filter(user=request.user).exists():
            pass 
        else:
            return redirect('/admin-login/')
        return super().dispatch(request,*args,**kwargs)


class AdminHomeView(AdminRequiredMixin,TemplateView):
    template_name='adminpages/adminhome.html'
    def get_context_data(self,**kwargs):
        context=super().get_context_data(**kwargs)
        context['pendingorders']=Order.objects.filter(order_status="Order Received").order_by('-id')
        return context

class AdminOrderDetailView(AdminRequiredMixin,DetailView):
    template_name='adminpages/adminorderdetail.html'
    model=Order
    context_object_name='ord_obj'

    def get_context_data(self,**kwargs):
        context=super().get_context_data(**kwargs)
        context['allstatus']=ORDER_STATUS
        return context

class AdminOrderListView(AdminRequiredMixin,ListView):
    template_name='adminpages/adminorderlist.html'
    queryset=Order.objects.all().order_by('-id')
    print(queryset)
    context_object_name='allorders'

class AdminOrderStatusView(AdminRequiredMixin,View):
    def post(self,request,*args,**kwargs):
        order_id=self.kwargs['pk']
        order_obj=Order.objects.get(id=order_id)
        new_status=request.POST['status']
        order_obj.order_status=new_status
        order_obj.save()
        return redirect(reverse_lazy('ecomapp:adminorderdetail',kwargs={'pk':order_id}))