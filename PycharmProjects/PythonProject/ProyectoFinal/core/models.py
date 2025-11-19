from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.urls import reverse

# NOTA: usamos settings.AUTH_USER_MODEL directamente en las ForeignKey,
# esto evita problemas con inspecciones estáticas que no reconocen alias como 'User = ...'

class Event(models.Model):
    """
    Un evento deportivo.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)  # None = sin límite
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.tickets = None
        self.id = None

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('event_detail', args=[str(self.id)])

    def tickets_sold(self) -> int:
        """
        Retorna la suma total de 'quantity' vendida para este evento.
        """
        agg = self.tickets.aggregate(total=Sum('quantity'))
        total = agg.get('total') or 0
        return int(total)

    def seats_available(self):
        """
        Retorna el número de asientos disponibles o None si no hay límite.
        """
        if self.capacity is None:
            return None
        sold = self.tickets.aggregate(total=Sum('quantity')).get('total') or 0
        available = self.capacity - int(sold)
        return max(available, 0)


class EventAdmin(models.Model):
    """
    Asociación entre usuario y evento (un usuario puede administrar muchos eventos).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_admin_roles')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='admins')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')
        verbose_name = "Administrador de Evento"
        verbose_name_plural = "Administradores de Evento"

    def __str__(self):
        # Si la inspección no encuentra 'username' puedes usar getattr para evitar warnings
        username = getattr(self.user, 'username', str(self.user))
        return f"{username} — admin de {self.event.title}"


class Ticket(models.Model):
    """
    Boleta/Inscripción comprada por un usuario para un evento.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_PAID = 'PAID'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_PAID, 'Pagada'),
        (STATUS_CANCELLED, 'Cancelada'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.id = None

    def __str__(self):
        buyer_name = getattr(self.buyer, 'username', str(self.buyer))
        return f"Ticket #{self.id} | {buyer_name} → {self.event.title}"
