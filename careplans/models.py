import uuid

from django.db import models


class Provider(models.Model):
    name = models.CharField(max_length=255)
    npi = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.name} ({self.npi})"


class Patient(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    mrn = models.CharField(max_length=64, unique=True)
    date_of_birth = models.DateField()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.mrn})"


class Order(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="orders")
    medication_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.medication_name} for {self.patient_id} @ {self.created_at}"


class CarePlan(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    history = models.JSONField(default=list)
    payload = models.JSONField(default=dict)
    care_plan = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    queued_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

