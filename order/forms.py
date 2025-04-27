from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    DIVISION_CHOICES = (
        ('Coastal Andhra', 'Coastal Andhra'),
        ('Rayalaseema', 'Rayalaseema'),
    )

    division = forms.ChoiceField(choices=DIVISION_CHOICES)
    district = forms.CharField(widget=forms.Select())  # JS will populate this
    zip_code = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
   
    class Meta:
        model = Order
        fields = ['name', 'email', 'phone', 'address', 'division', 'district', 'zip_code','razorpay_order_id']
