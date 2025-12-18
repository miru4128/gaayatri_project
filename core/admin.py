from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, FarmerProfile, DoctorProfile, Cattle


class FarmerProfileInline(admin.StackedInline):
	model = FarmerProfile
	can_delete = False
	extra = 0
	max_num = 1

	def get_extra(self, request, obj=None, **kwargs):
		if obj:
			try:
				obj.farmerprofile  # type: ignore[attr-defined]
			except FarmerProfile.DoesNotExist:
				return 1
		return 0


class DoctorProfileInline(admin.StackedInline):
	model = DoctorProfile
	can_delete = False
	extra = 0
	max_num = 1

	def get_extra(self, request, obj=None, **kwargs):
		if obj:
			try:
				obj.doctorprofile  # type: ignore[attr-defined]
			except DoctorProfile.DoesNotExist:
				return 1
		return 0


class CattleInline(admin.TabularInline):
	model = Cattle
	extra = 0
	fields = ('tag_number', 'name', 'breed', 'age_years', 'daily_milk_yield', 'last_vaccination_date')
	readonly_fields = ()
	fk_name = 'owner'

	def has_add_permission(self, request, obj=None):
		return bool(obj and getattr(obj, 'is_farmer', False))

	def has_change_permission(self, request, obj=None):
		return bool(obj and getattr(obj, 'is_farmer', False))

	def has_delete_permission(self, request, obj=None):
		return bool(obj and getattr(obj, 'is_farmer', False))


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	list_display = (
		'username',
		'email',
		'is_farmer',
		'is_doctor',
		'is_staff',
		'is_active',
	)
	list_filter = (*BaseUserAdmin.list_filter, 'is_farmer', 'is_doctor')
	inlines = [FarmerProfileInline, DoctorProfileInline, CattleInline]

	fieldsets = (*BaseUserAdmin.fieldsets, ('Gaayatri Roles', {'fields': ('is_farmer', 'is_doctor')}))
	add_fieldsets = (*BaseUserAdmin.add_fieldsets, ('Gaayatri Roles', {'fields': ('is_farmer', 'is_doctor')}))

	def get_inline_instances(self, request, obj=None):
		if obj is None:
			return []
		instances = []
		for inline_class in self.inlines:
			if inline_class is CattleInline and not getattr(obj, 'is_farmer', False):
				continue
			instances.append(inline_class(self.model, self.admin_site))
		return instances


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'farm_name', 'location')
	search_fields = ('user__username', 'user__email', 'farm_name', 'location')
	autocomplete_fields = ('user',)


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'specialization', 'license_number')
	search_fields = ('user__username', 'user__email', 'specialization', 'license_number')
	autocomplete_fields = ('user',)


@admin.register(Cattle)
class CattleAdmin(admin.ModelAdmin):
	list_display = ('name', 'tag_number', 'owner', 'breed', 'age_years', 'daily_milk_yield', 'last_vaccination_date')
	list_filter = ('breed', 'last_vaccination_date')
	search_fields = ('name', 'tag_number', 'breed', 'owner__username', 'owner__email')
	autocomplete_fields = ('owner',)
	list_select_related = ('owner',)