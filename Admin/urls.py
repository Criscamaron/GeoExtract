from django.urls import path
from Admin import views
urlpatterns = [
    path('trabajos/', views.listar_trabajos, name='listar_trabajos'),
    path('crear_trabajo/', views.crear_trabajo, name='crear_trabajo'),
    path('actualizar_trabajo/<int:id>/', views.actualizar_trabajo, name='actualizar_trabajo'),
    path('eliminar_trabajo/<int:id>/', views.eliminar_trabajo, name='eliminar_trabajo'),
    path('ver_mensajes/', views.ver_mensajes, name='ver_mensajes'),
    path('manejar_mensaje/<int:mensaje_id>/<str:accion>/', views.manejar_mensaje, name='manejar_mensaje'),
    path('documentacion/', views.documentacion, name='documentacion'),
    path('graficos/productividad/', views.productividad, name='graficos_productividad'),
    path('graficos/asistencias/', views.asistencias, name='graficos_asistencias'),
]