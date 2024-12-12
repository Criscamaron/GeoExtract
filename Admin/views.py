from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from GeoExtract.settings import SECRET_KEYSUPABASE, SECRET_URLSUPABASE

# Crear cliente de Supabase
import supabase
supabase = supabase.create_client(SECRET_URLSUPABASE, SECRET_KEYSUPABASE)

@login_required
def crear_trabajo(request):
    """Crear un nuevo trabajo y asignar empleados."""
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        tipo = request.POST.get("tipo")
        descripcion = request.POST.get("descripcion")
        empleado_asignado = request.POST.get("empleado_asignado")  # Solo un empleado

        # Validar campos
        if not (nombre and tipo and descripcion and empleado_asignado):
            return HttpResponse("Todos los campos son obligatorios", status=400)

        # Insertar trabajo en Supabase
        data = {
            'nombre': nombre,
            'tipo': tipo,
            'descripcion': descripcion,
            'empleado_asignado': empleado_asignado
        }
        response = supabase.table('trabajo').insert([data]).execute()

        # Verificar la respuesta
        if response.data:
            return redirect('/trabajos/trabajos')
        else:
            return HttpResponse(f"Error al crear el trabajo: {response.error}", status=400)

    # Obtener lista de empleados para asignación
    empleados = supabase.table('empleados').select('*').execute()
    return render(request, 'Admin/crear_trabajo.html', {
        'empleados': empleados.data,
        'titulo': 'Crear Trabajo',
        'desc': 'Crea un trabajo'
    })


@login_required
def listar_trabajos(request):
    """Listar todos los trabajos."""
    tipo = request.GET.get('tipo', None)
    if tipo:
        response = supabase.table('trabajo').select('*').eq('tipo', tipo).execute()
    else:
        response = supabase.table('trabajo').select('*').execute()


    trabajos = response.data

    # Enriquecer con detalles de empleados
    for trabajo in trabajos:
        empleado_id = trabajo.get('empleado_asignado')
        if empleado_id:
            empleado_response = supabase.table('empleados').select('*').eq('id', empleado_id).execute()
            trabajo['empleado_asignado_detalle'] = empleado_response.data[0] if empleado_response.data else None
        else:
            trabajo['empleado_asignado_detalle'] = None

    return render(request, 'Admin/trabajo.html', {
        'trabajos': trabajos,
        'tipo': tipo
    })


@login_required
def actualizar_trabajo(request, id):
    """Actualizar un trabajo existente."""
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        tipo = request.POST.get("tipo")
        descripcion = request.POST.get("descripcion")
        empleado_asignado = request.POST.get("empleado_asignado")  # Solo un empleado

        # Validar campos
        if not (nombre and tipo and descripcion):
            return HttpResponse("Todos los campos son obligatorios", status=400)

        # Datos a actualizar
        data = {
            'nombre': nombre,
            'tipo': tipo,
            'descripcion': descripcion,
            'empleado_asignado': empleado_asignado
        }

        # Actualizar trabajo en Supabase
        response = supabase.table('trabajo').update(data).eq('id', id).execute()

        if response.data:
            return redirect('/trabajos/trabajos')
        else:
            return HttpResponse(f"Error al actualizar el trabajo: {response.error}", status=400)

    # Obtener los datos actuales del trabajo
    response = supabase.table('trabajo').select('*').eq('id', id).execute()
    trabajo = response.data[0] if response.data else None

    if not trabajo:
        return HttpResponse("Trabajo no encontrado", status=404)

    # Obtener lista de empleados para asignación
    empleados = supabase.table('empleados').select('*').execute()
    return render(request, 'Admin/crear_trabajo.html', {
        'trabajo': trabajo,
        'empleados': empleados.data,
        'titulo': 'Actualizar Trabajo',
        'desc': 'Edita los detalles del trabajo'
    })


@login_required
def eliminar_trabajo(request, id):
    """Eliminar un trabajo existente."""
    response = supabase.table('trabajo').delete().eq('id', id).execute()

    if response.data:
        return redirect('/trabajos/trabajos')
    else:
        return HttpResponse(f"Error al eliminar el trabajo: {response.error}", status=400)
    
@login_required
def ver_mensajes(request):
    # Obtener los mensajes pendientes
    response = supabase.table('mensajes').select('*').eq('estado', 'pendiente').execute()
    
    mensajes = response.data

    # Crear una lista con los mensajes con los datos del empleado
    for mensaje in mensajes:
        # Obtener el nombre del empleado basado en su ID
        empleado_response = supabase.table('empleados').select('nombre').eq('id', mensaje['id_empleado']).execute()
        
        if empleado_response.data:
            # Asignamos el nombre del empleado al mensaje
            mensaje['empleado_nombre'] = empleado_response.data[0]['nombre']
        else:
            # Si no encontramos al empleado, asignamos un nombre genérico o vacío
            mensaje['empleado_nombre'] = "Desconocido"
    
    return render(request, 'Admin/ver_mensajes.html', {'mensajes': mensajes})

@login_required
def manejar_mensaje(request, mensaje_id, accion):
    # Actualizar el estado del mensaje
    nuevo_estado = 'aprobado' if accion == 'aprobar' else 'rechazado'

    response = supabase.table('mensajes').update({'estado': nuevo_estado}).eq('id', mensaje_id).execute()

    return redirect('ver_mensajes')

@login_required
def asistencias(request):
    # Obtener todas las asistencias desde Supabase
    response = supabase.table('asistencia').select('*').execute()

    if response.data:
        # Contamos cuántas asistencias están marcadas y cuántas no
        marcadas = sum(1 for asistencia in response.data if asistencia['fecha_asistencia'] is not None)
        no_marcadas = len(response.data) - marcadas

        # Datos para el gráfico
        asistencias = {
            'marcadas': marcadas,
            'no_marcadas': no_marcadas
        }

        return render(request, 'Admin/graficos.html', {'asistencias': asistencias})
    else:
        return render(request, 'Admin/graficos.html', {'asistencias': {'marcadas': 0, 'no_marcadas': 0}})

@login_required
def productividad(request):
    # Obtener todas las tareas de la tabla 'trabajo' desde Supabase
    response = supabase.table('trabajo').select('*').execute()

    if response.data:
        # Contamos cuántas tareas están completadas y cuántas pendientes
        completadas = sum(1 for tarea in response.data if tarea['completado'])
        pendientes = len(response.data) - completadas

        # Datos para el gráfico
        tareas = {
            'completadas': completadas,
            'pendientes': pendientes
        }

        return render(request, 'Admin/graficos.html', {'tareas': tareas})
    else:
        return render(request, 'Admin/graficos.html', {'tareas': {'completadas': 0, 'pendientes': 0}})

import random 
@login_required
def documentacion(request):
    # Ejemplo de datos de productividad (tareas totales, completadas y pendientes)
    tareas_totales = 50
    tareas_completadas = random.randint(10, 50)  # Tareas completadas aleatorias
    tareas_pendientes = tareas_totales - tareas_completadas
    
    # Ejemplo de datos de asistencia
    asistencia_hoy = random.randint(30, 50)  # Asistencia de hoy
    asistencia_total = 50  # Total de empleados
    asistencia_faltante = asistencia_total - asistencia_hoy
    
    return render(request, 'Admin/graficos.html', {
        'tareas_totales': tareas_totales,
        'tareas_completadas': tareas_completadas,
        'tareas_pendientes': tareas_pendientes,
        'asistencia_hoy': asistencia_hoy,
        'asistencia_faltante': asistencia_faltante,
        'asistencia_total': asistencia_total,
    })
