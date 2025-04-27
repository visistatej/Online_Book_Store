from django.shortcuts import HttpResponse, render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.views import View
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from cart.cart import Cart
from .models import Order, OrderItem
from .forms import OrderCreateForm
from .pdfcreator import renderPdf
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import razorpay
from .models import Order
from django.conf import settings
from django.core.validators import RegexValidator

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))

@csrf_exempt
def create_order_ajax(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)

        cart = Cart(request)
        total_price = cart.get_total_price()

        phone_validator = RegexValidator(
            regex=r'^[6-9]\d{9}$',
            message='Enter a valid 10-digit phone number starting with 6-9.'
        )
        try:
            phone_validator(data['phone'])  
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)

        order = Order.objects.create(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            address=data['address'],
            division=data['division'],
            district=data['district'],
            zip_code=data['zip_code'],
            totalbook=len(cart),
            payable=total_price,
			customer=request.user if request.user.is_authenticated else None
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                book=item['book'],
                price=item['price'],
                quantity=item['quantity']
            )

        cart.clear()

        client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
        razorpay_order = client.order.create({
            'amount': int(total_price * 100),
            'currency': 'INR',
            'payment_capture': 1
        })

        order.razorpay_order_id = razorpay_order['id']
        order.save()

        return JsonResponse({
            'order_id': razorpay_order['id'],
            'amount': int(total_price * 100),
        })

def order_create(request):
	cart = Cart(request)
	if request.user.is_authenticated:
		customer = get_object_or_404(User, id=request.user.id)
		form = OrderCreateForm(request.POST or None, initial={"name": customer.first_name, "email": customer.email})
		if request.method == 'POST':
			if form.is_valid():
				order = form.save(commit=False)
				order.customer = User.objects.get(id=request.user.id)
				order.payable = cart.get_total_price()
				order.totalbook = len(cart) # len(cart.cart) // number of individual book
				order.save()

				for item in cart:
					OrderItem.objects.create(
						order=order, 
						book=item['book'], 
						price=item['price'], 
						quantity=item['quantity']
						)
				cart.clear()
				return render(request, 'order/successfull.html', {'order': order})

			else:
				messages.error(request, "Fill out your information correctly.")

		if len(cart) > 0:
			return render(request, 'order/order.html', {"form": form})
		else:
			return redirect('store:books')
	else:
		return redirect('store:signin')
			
def order_list(request):
	my_order = Order.objects.filter(customer_id = request.user.id).order_by('-created')
	paginator = Paginator(my_order, 4)
	page = request.GET.get('page')
	myorder = paginator.get_page(page)

	return render(request, 'order/list.html', {"myorder": myorder})

def order_details(request, id):
	order_summary = get_object_or_404(Order, id=id)

	if order_summary.customer_id != request.user.id:
		return redirect('store:index')

	orderedItem = OrderItem.objects.filter(order_id=id)
	context = {
		"o_summary": order_summary,
		"o_item": orderedItem
	}
	return render(request, 'order/details.html', context)

class pdf(View):
    def get(self, request, id):
        try:
            query=get_object_or_404(Order,id=id)
        except:
            Http404('Content not found')
        context={
            "order":query
        }
        article_pdf = renderPdf('order/pdf.html',context)
        return HttpResponse(article_pdf,content_type='application/pdf')

def payment_success(request):
    order_id = request.GET.get('order_id')
    payment_id = request.GET.get('payment_id')

    if not order_id or not payment_id:
        messages.error(request, "Invalid payment confirmation.")
        return redirect('store:index')

    try:
        order = Order.objects.get(razorpay_order_id=order_id)
        order.paid = True
        order.save()
        return render(request, 'order/successfull.html', {'order': order})
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('store:index')