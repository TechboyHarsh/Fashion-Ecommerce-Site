from django.contrib import admin
from . models import Contact,User,Product,Wishlist,Cart,Transaction
# Register your models here.
admin.site.site_header = "Website By Harsh"

class AdminContact(admin.ModelAdmin):
    list_display = ('name', 'email', 'mobile', 'remarks')
    list_filter=('name',)

admin.site.register(Contact,AdminContact)
admin.site.register(User)
admin.site.register(Product)
admin.site.register(Wishlist)
admin.site.register(Cart)
admin.site.register(Transaction)