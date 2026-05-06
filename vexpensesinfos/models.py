from django.db import models


class Project(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    cnpj = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    neighborhood = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    phone1 = models.CharField(max_length=20, null=True, blank=True)
    phone2 = models.CharField(max_length=20, null=True, blank=True)
    on = models.BooleanField(default=True)
    integration_id = models.CharField(max_length=100, null=True, blank=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vexpenses_project"

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    id = models.IntegerField(primary_key=True)
    integration_id = models.CharField(max_length=100, null=True, blank=True)
    external_id = models.CharField(max_length=100, null=True, blank=True)
    company_id = models.IntegerField()
    role_id = models.IntegerField(null=True, blank=True)
    approval_flow_id = models.IntegerField(null=True, blank=True)
    expense_limit_policy_id = models.IntegerField(null=True, blank=True)
    user_type = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, null=True, blank=True)
    cpf = models.CharField(max_length=20, null=True, blank=True)
    phone1 = models.CharField(max_length=20, null=True, blank=True)
    phone2 = models.CharField(max_length=20, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    bank = models.CharField(max_length=100, null=True, blank=True)
    agency = models.CharField(max_length=50, null=True, blank=True)
    account = models.CharField(max_length=50, null=True, blank=True)
    pix_key = models.CharField(max_length=100, null=True, blank=True)
    confirmed = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    projects = models.ManyToManyField(Project, blank=True, related_name="members")
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vexpenses_team_member"

    def __str__(self):
        return self.name


class ExpenseType(models.Model):
    id = models.IntegerField(primary_key=True)
    integration_id = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=255)
    on = models.BooleanField(default=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vexpenses_expense_type"

    def __str__(self):
        return self.description


class Expense(models.Model):
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(
        TeamMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
        db_column="user_id",
    )
    expense_id = models.IntegerField(null=True, blank=True)  # report id reference
    device_id = models.IntegerField(null=True, blank=True)
    integration_id = models.CharField(max_length=100, null=True, blank=True)
    external_id = models.CharField(max_length=100, null=True, blank=True)
    mileage = models.FloatField(null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    expense_type_id = models.IntegerField(null=True, blank=True)
    payment_method_id = models.IntegerField(null=True, blank=True)
    paying_company_id = models.IntegerField(null=True, blank=True)
    course_id = models.IntegerField(null=True, blank=True)
    receipt_url = models.TextField(null=True, blank=True)
    value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    validate = models.CharField(max_length=10, null=True, blank=True)
    reimbursable = models.BooleanField(default=False)
    observation = models.TextField(null=True, blank=True)
    rejected = models.BooleanField(default=False)
    on = models.BooleanField(default=True)
    mileage_value = models.FloatField(null=True, blank=True)
    original_currency_iso = models.CharField(max_length=10, null=True, blank=True)
    exchange_rate = models.FloatField(null=True, blank=True)
    converted_value = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    converted_currency_iso = models.CharField(max_length=10, null=True, blank=True)
    # Report fields (embedded, not FK)
    report_id = models.IntegerField(null=True, blank=True)
    report_status = models.CharField(max_length=50, null=True, blank=True)
    report_description = models.TextField(null=True, blank=True)

    # Apportionment fields
    apportionment_company_id = models.IntegerField(null=True, blank=True)
    apportionment_description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vexpenses_expense"

    def __str__(self):
        return f"{self.title} - {self.value}"