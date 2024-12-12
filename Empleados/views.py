from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden
from GeoExtract.settings import SECRET_KEYSUPABASE, SECRET_URLSUPABASE
import supabase
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout, authenticate
from django.contrib.auth.models import User
supabase = supabase.create_client(SECRET_URLSUPABASE, SECRET_KEYSUPABASE)

def inicio(request):
    if request.user.is_superuser:
        return render(request, 'Admin/administrador.html')
    return render(request, 'index.html')

def exit(request):
    logout(request)  # Cierra la sesión del usuario
    return redirect('login')  # Redirige a la página de login
    
def es_admin(user):
    return user.is_superuser  # Retorna True si el usuario es un superusuario

@login_required
@user_passes_test(es_admin)  # Restringe el acceso solo a administradores
def administrador(request):
    # Aquí puedes añadir lógica adicional si es necesario, como recuperar datos específicos
    return render(request, 'Admin/administrador.html')  

def login(request):
    if request.user.is_authenticated:
        # Redirige al lugar adecuado según el tipo de usuario
        if request.user.is_superuser:
            return redirect('administrador')
        return redirect('inicio')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            auth_login(request, user)
            return redirect('inicio' if not user.is_superuser else 'administrador')
        return render(request, 'login.html', {'error': 'Credenciales incorrectas'})

    return render(request, 'login.html')

@login_required
def empleados(request):
    response = supabase.table('empleados').select('*, cargo(nombre), departamento(nombre)').execute()  # Seleccionar todos los campos de empleados y los nombres de cargo y departamento
    empleados = response.data
    return render(request, 'Admin/empleado.html', {'empleados': empleados})

@login_required
def crear_empleado(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
    
    # Obtener cargos y departamentos
    cargos = supabase.table('cargo').select('*').execute().data
    departamentos = supabase.table('departamento').select('*').execute().data

    if request.method == 'POST':
        # Datos del formulario
        data = {
            'run': request.POST.get('run'),
            'nombre': request.POST.get('nombre'),
            'apellido': request.POST.get('apellido'),
            'contraseña': request.POST.get('nombre') + "12345",
            'correo': request.POST.get('correo'),
            'fecha_nacimiento': request.POST.get('fecha_nacimiento'),
            'sueldo': request.POST.get('sueldo'),
            'cargo_id': request.POST.get('cargo'),
            'departamento_id': request.POST.get('departamento'),
        }

        # Validar si el RUN ya existe en Supabase
        existing_empleado = supabase.table('empleados').select('*').eq('run', data['run']).execute()
        if existing_empleado.data:
            return HttpResponse("El RUN ya existe. Por favor, ingrese un RUN diferente.", status=400)

        # Validar si el correo ya existe en Django
        if User.objects.filter(email=data['correo']).exists():
            return HttpResponse("El correo ya está registrado en el sistema. Por favor, ingrese un correo diferente.", status=400)

        # Insertar empleado en Supabase
        response = supabase.table('empleados').insert([data]).execute()
        if not response.data:
            return HttpResponse(f"Error al crear empleado: {response.error}", status=400)

        # Usar la ID de Supabase para crear el usuario en Django
        supabase_id = response.data[0]['id']
        try:
            username = data['run']  # Usamos el RUN como nombre de usuario
            password = data['contraseña']
            user = User.objects.create_user(
                id=supabase_id,
                username=username,
                password=password,
                email=data['correo'],
                first_name=data['nombre'],
                last_name=data['apellido']
            )
            user.save()
        except Exception as e:
            return HttpResponse(f"Error al crear el usuario en Django: {str(e)}", status=500)

        return redirect('empleados')

    return render(request, 'Admin/crear_empleado.html', {
        'cargos': cargos,
        'departamentos': departamentos
    })

@login_required
def actualizar_empleado(request, id):
    cargos = supabase.table('cargo').select('*').execute().data
    departamentos = supabase.table('departamento').select('*').execute().data

    if request.method == 'POST':
        data = {
            'run': request.POST.get('run'),
            'nombre': request.POST.get('nombre'),
            'apellido': request.POST.get('apellido'),
            'fecha_nacimiento': request.POST.get('fecha_nacimiento'),
            'correo':request.POST.get('correo'),
            'sueldo': request.POST.get('sueldo'),
            'cargo_id': request.POST.get('cargo'),
            'departamento_id': request.POST.get('departamento'),
        }

        # Actualizar en Supabase
        response = supabase.table('empleados').update(data).eq('id', id).execute()
        if not response.data:
            return HttpResponse(f"Error al actualizar empleado: {response.error}", status=400)

        # Actualizar en Django (si el correo, nombre o apellido cambian)
        try:
            user = User.objects.get(id=id)
            user.email = data['correo']
            user.password = data['nombre'] + "12345"
            user.first_name = data['nombre']
            user.last_name = data['apellido']
            user.save()
        except User.DoesNotExist:
            return HttpResponse("Error: Usuario no encontrado en Django.", status=404)

        return redirect('empleados')

    # Obtener datos actuales del empleado
    empleado = supabase.table('empleados').select('*').eq('id', id).single().execute()
    if not empleado.data:
        return HttpResponse("Empleado no encontrado", status=404)

    return render(request, 'Admin/crear_empleado.html', {
        'empleado': empleado.data,
        'cargos': cargos,
        'departamentos': departamentos
    })

@login_required
def eliminar_empleado(request, id):
    # Eliminar de Supabase
    response = supabase.table('empleados').delete().eq('id', id).execute()
    if not response.data:
        return HttpResponse("Error al eliminar el empleado en Supabase.", status=400)

    # Eliminar de Django
    try:
        user = User.objects.get(id=id)
        user.delete()
    except User.DoesNotExist:
        return HttpResponse("Error: Usuario no encontrado en Django.", status=404)

    return redirect('empleados')


@login_required
def crear_cargo(request):
    if request.method == "POST":
        nombre = request.POST.get("cargo_nombre")
        if nombre:
            existing_cargo = supabase.table('cargo').select('*').eq('nombre', nombre).execute()
            if existing_cargo.data:
                return render(request, 'Admin/gestionar_cargos_y_departamentos.html', {
                    'mensaje': 'El cargo ya existe.',
                    'cargos': supabase.table('cargo').select('*').execute().data,
                    'departamentos': supabase.table('departamento').select('*').execute().data
                })
            data = {'nombre': nombre}
            response = supabase.table('cargo').insert([data]).execute()
            return redirect('gestionar_cargos_y_departamentos')
        else:
            return HttpResponse("El nombre es obligatorio", status=400)

    return redirect('gestionar_cargos_y_departamentos')
@login_required
def crear_departamento(request):
    if request.method == "POST":
        nombre = request.POST.get("departamento_nombre")
        if nombre:
            data = {'nombre': nombre}
            response = supabase.table('departamento').insert([data]).execute()
            return redirect('gestionar_cargos_y_departamentos')
        else:
            return HttpResponse("El nombre es obligatorio", status=400)
    return redirect('gestionar_cargos_y_departamentos')
@login_required
def gestionar_cargos_y_departamentos(request):
    cargos = supabase.table('cargo').select('*').execute().data 
    departamentos = supabase.table('departamento').select('*').execute().data  
    return render(request, 'Admin/gestionar_cargos_y_departamentos.html', {
        'cargos': cargos,
        'departamentos': departamentos
    })
@login_required
def eliminar_cargo(request, id):
    response = supabase.table('cargo').delete().eq('id', id).execute()
    return redirect('gestionar_cargos_y_departamentos')

@login_required
def eliminar_departamento(request, id):
    response = supabase.table('departamento').delete().eq('id', id).execute()
    return redirect('gestionar_cargos_y_departamentos')

def marcar_completado(request, trabajo_id):
    # Obtener el trabajo desde Supabase
    trabajo_response = supabase.table('trabajo').select('*').eq('id', trabajo_id).execute()
    
    if trabajo_response.data:
        trabajo = trabajo_response.data[0]
        # Cambiar el estado de completado (alternar entre True/False)
        completado_nuevo = not trabajo['completado']
        
        # Actualizar el trabajo en Supabase
        update_response = supabase.table('trabajo').update({'completado': completado_nuevo}).eq('id', trabajo_id).execute()
        
        return redirect(reverse('listar_trabajos_empleado', args=[trabajo['empleado_asignado']]))
        
    else:
        return HttpResponse("Trabajo no encontrado.", status=404)

def listar_trabajos_empleados(request, id):
    # Consultar los trabajos asociados al empleado usando Supabase
    response = supabase.table('trabajo').select('*').eq('empleado_asignado', id).execute()

    trabajos = response.data  # Lista de trabajos del empleado

    # Renderizar la plantilla con los datos
    return render(request, 'Empleados/listar_trabajos.html', {
        'trabajos': trabajos,
        'empleado_id': id,  # Pasar el id del empleado al template
    })
    
@login_required
def marcar_asistencia(request, id):
        empleado_id = id  # Usar el id pasado como parámetro
        fecha_asistencia = datetime.today().date()  # Obtener la fecha de hoy

        # Convertir la fecha de tipo date a string (YYYY-MM-DD)
        fecha_asistencia_str = fecha_asistencia.strftime('%Y-%m-%d')

        # Preparamos los datos para insertar
        data = {
            'fecha_asistencia': fecha_asistencia_str,
            'id_empleado': empleado_id
        }

        # Insertar la asistencia en la tabla 'asistencia' de Supabase
        response = supabase.table('asistencia').insert([data]).execute()


        return redirect(reverse('listar_asistencia', args=[empleado_id]))



def listar_asistencia(request, id): # Obtener el ID del empleado desde el usuario autenticado
    fecha_hoy = datetime.today().date()  # Fecha de hoy

    # Verificar si ya existe un registro de asistencia para hoy
    response = supabase.table('asistencia').select('*').eq('id_empleado', id).eq('fecha_asistencia', str(fecha_hoy)).execute()

    if response.data:
        asistencia = True  # El empleado ya ha marcado asistencia
    else:
        asistencia = False  # El empleado no ha marcado asistencia aún

    # Renderizar la página de asistencia con el estado de asistencia de hoy
    return render(request, 'Empleados/asistencia/asistencia.html', {
        'asistencia': asistencia,  # Pasamos si el empleado ya marcó asistencia hoy
    })
    
@login_required
def enviar_mensaje(request):
    if request.method == "POST":
        contenido = request.POST.get("contenido")

        if contenido:
            empleado_id = request.user.id  # Obtener el ID del usuario autenticado

            # Insertar el mensaje en la tabla de mensajes
            response = supabase.table('mensajes').insert([{
                'contenido': contenido, 
                'id_empleado': empleado_id
            }]).execute()

            if response.data:
                # Redirigir a la vista donde se listan los mensajes del empleado
                return redirect(reverse('listar_mensaje', args=[empleado_id]))
            else:
                return render(request, 'Empleados/enviar_mensajes.html', {'error': 'Hubo un error al enviar el mensaje.'})

    return render(request, 'Empleados/enviar_mensajes.html')

@login_required
def ver_mensajes_usuario(request, id):
    # Obtener el ID del usuario autenticado
    empleado_id = id 

    # Obtener los mensajes del empleado específico que están pendientes
    response = supabase.table('mensajes').select('*').eq('id_empleado', empleado_id).execute()

    # Filtrar los mensajes por estado si es necesario, por ejemplo, 'pendiente', 'aprobado' o 'rechazado'
    mensajes = response.data

    # Pasar los mensajes filtrados a la plantilla
    return render(request, 'Empleados/listar_mensajes.html', {'mensajes': mensajes})
