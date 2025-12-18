from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_farmer = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)

# Simple profiles to hold extra data later
class FarmerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    farm_name = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    specialization = models.CharField(max_length=100, default="General Veterinary")
    license_number = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.user.username
    
# --- Append this to core/models.py ---

class Cattle(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    tag_number = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100)
    age_years = models.PositiveIntegerField()
    daily_milk_yield = models.FloatField(help_text="In Liters")
    last_vaccination_date = models.DateField(null=True, blank=True)
    is_sick = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.tag_number})"

class FinancialRecord(models.Model):
    RECORD_TYPES = [('income', 'Income'), ('expense', 'Expense')]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    type = models.CharField(max_length=10, choices=RECORD_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200) # e.g., "Sold Milk", "Bought Feed"

    def __str__(self):
        return f"{self.type} - {self.amount}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    body = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} to {self.recipient}"
    
    class Meta:
        ordering = ['timestamp']

# core/models.py

# ... keep your existing User and Cattle models ...

class InventoryItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    quantity = models.FloatField(help_text="Current stock in kg or units")
    reorder_level = models.FloatField(help_text="Alert when stock drops below this")
    daily_usage_rate = models.FloatField(default=0.0, help_text="Average daily consumption (kg/units)")
    last_updated = models.DateTimeField(auto_now=True)

    def days_remaining(self):
        if self.daily_usage_rate > 0:
            return round(self.quantity / self.daily_usage_rate, 1)
        return "Unknown (Set usage rate)"

    def __str__(self):
        return self.item_name

class InventoryHistory(models.Model):
    TRANSACTION_TYPES = [('ADD', 'Stock Added'), ('CONSUME', 'Stock Consumed')]
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity_changed = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.item.item_name} - {self.action} {self.quantity_changed}"