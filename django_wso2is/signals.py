"""Module containing custom django signals."""
import django.dispatch

user_authenticated = django.dispatch.Signal()
