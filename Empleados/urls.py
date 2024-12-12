from django.urls import path
from Empleados import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('listar_trabajos_empleado/<int:id>/', views.listar_trabajos_empleados, name='listar_trabajos_empleado'),
    path('trabajos/completado/<int:trabajo_id>/', views.marcar_completado, name='marcar_completado'),
    path('empleados/', views.empleados, name='empleados'),
    path('crear_empleado/', views.crear_empleado, name='crear_empleado'),
    path('actualizar_empleado/<int:id>/', views.actualizar_empleado, name='actualizar_empleado'),
    path('eliminar_empleado/<int:id>/', views.eliminar_empleado, name='eliminar_empleado'),
    path('gestionar_cargos_y_departamentos/', views.gestionar_cargos_y_departamentos, name='gestionar_cargos_y_departamentos'),
    path('crear_cargo/', views.crear_cargo, name='crear_cargo'),
    path('eliminar_cargo/<int:id>/', views.eliminar_cargo, name='eliminar_cargo'),
    path('crear_departamentos/', views.crear_departamento, name='crear_departamento'),
    path('eliminar_departamentos/<int:id>/', views.eliminar_departamento, name='eliminar_departamento'),
    path('listar_asistencia/<int:id>/', views.listar_asistencia, name='listar_asistencia'),
    path('marcar_asistencia/<int:id>/', views.marcar_asistencia, name='marcar_asistencia'),
    path('enviar_mensaje/', views.enviar_mensaje, name='enviar_mensaje'),
    path('listar_mensaje/<int:id>/', views.ver_mensajes_usuario, name='listar_mensaje'),
    path('logout/', views.exit, name='exit'),
]



