# app_Libreria/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import *

# =============================================
# DECORADORES PERSONALIZADOS
# =============================================

def es_administrador(user):
    return user.is_authenticated and user.is_staff

def es_cliente(user):
    return user.is_authenticated and not user.is_staff

def crear_perfil_cliente(user):
    """Crear perfil de cliente automáticamente cuando un usuario se registra"""
    if not hasattr(user, 'cliente'):
        Cliente.objects.create(
            user=user,
            telefono='',
            direccion='',
            preferenciasgenero=''  # CORREGIDO: sin guión
        )

# =============================================
# VISTAS PÚBLICAS
# =============================================

def inicio(request):
    try:
        # Filtrar solo libros con libroid válido
        libros = Libro.objects.filter(stock__gt=0).exclude(libroid__isnull=True)[:8]
        return render(request, 'inicio.html', {'libros': libros})
    except Exception as e:
        print(f"Error en vista inicio: {e}")
        return render(request, 'inicio.html', {'libros': []})

def libros(request):
    try:
        # Filtrar solo libros con libroid válido y stock
        libros_lista = Libro.objects.filter(stock__gt=0).exclude(libroid__isnull=True)
        return render(request, 'libros.html', {'libros': libros_lista})
    except Exception as e:
        print(f"Error en vista libros: {e}")
        return render(request, 'libros.html', {'libros': []})

def eventos(request):
    eventos_lista = Evento.objects.filter(activo=True)
    return render(request, 'eventos.html', {'eventos': eventos_lista})

def blog(request):
    entradas = Blog.objects.filter(activo=True)
    return render(request, 'blog.html', {'entradas': entradas})

def contacto(request):
    return render(request, 'contacto.html')

# =============================================
# VISTAS DE AUTENTICACIÓN
# =============================================

def login_selector(request):
    return render(request, 'auth/login_selector.html')

def login_cliente(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None and not user.is_staff:
            login(request, user)
            # Crear perfil de cliente si no existe
            crear_perfil_cliente(user)
            messages.success(request, f'¡Bienvenido {user.username}!')
            return redirect('inicio')
        else:
            messages.error(request, 'Credenciales inválidas o no es una cuenta de cliente')
    
    return render(request, 'auth/login_cliente.html')

def login_admin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, f'¡Bienvenido Administrador {user.username}!')
            return redirect('panel_admin')
        else:
            messages.error(request, 'Credenciales inválidas o no tiene permisos de administrador')
    
    return render(request, 'auth/login_admin.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('inicio')

# =============================================
# PANEL ADMINISTRADOR
# =============================================

@login_required
@user_passes_test(es_administrador)
def panel_admin(request):
    stats = {
        'total_libros': Libro.objects.count(),
        'total_ventas': Venta.objects.count(),
        'total_usuarios': User.objects.count(),
        'total_eventos': Evento.objects.count(),
        'ventas_hoy': Venta.objects.filter(fechaventa__date=timezone.now().date()).count(),
        'ingresos_hoy': sum(venta.montototal for venta in Venta.objects.filter(fechaventa__date=timezone.now().date())),
    }
    return render(request, 'admin/panel_admin.html', {'stats': stats})

# =============================================
# CRUD AUTORES (ADMIN) - COMPLETO
# =============================================

@login_required
@user_passes_test(es_administrador)
def admin_autores(request):
    autores = Autor.objects.all()
    return render(request, 'admin/autores/listado.html', {'autores': autores})

@login_required
@user_passes_test(es_administrador)
def agregar_autor(request):
    if request.method == 'POST':
        try:
            # Verificar que todos los campos requeridos están presentes
            nombre = request.POST.get('nombre')
            apellido = request.POST.get('apellido')
            nacionalidad = request.POST.get('nacionalidad')
            fechanacimiento = request.POST.get('fechanacimiento')
            
            print(f"Debug - Campos recibidos:")
            print(f"Nombre: {nombre}")
            print(f"Apellido: {apellido}") 
            print(f"Nacionalidad: {nacionalidad}")
            print(f"Fecha Nacimiento: {fechanacimiento}")
            
            # Validar campos requeridos
            if not all([nombre, apellido, nacionalidad, fechanacimiento]):
                messages.error(request, 'Todos los campos marcados con * son obligatorios')
                return render(request, 'admin/autores/agregar.html')
            
            autor = Autor.objects.create(
                nombre=nombre,
                apellido=apellido,
                nacionalidad=nacionalidad,
                fechanacimiento=fechanacimiento,
                bibliografia=request.POST.get('bibliografia', ''),
                paginaweb=request.POST.get('paginaweb', '')
            )
            messages.success(request, 'Autor agregado correctamente')
            return redirect('admin_autores')
        except Exception as e:
            messages.error(request, f'Error al agregar autor: {str(e)}')
    
    return render(request, 'admin/autores/agregar.html')

@login_required
@user_passes_test(es_administrador)
def editar_autor(request, id):
    autor = get_object_or_404(Autor, autorid=id)
    
    if request.method == 'POST':
        try:
            autor.nombre = request.POST.get('nombre')
            autor.apellido = request.POST.get('apellido')
            autor.nacionalidad = request.POST.get('nacionalidad')
            autor.fechanacimiento = request.POST.get('fechanacimiento')
            autor.bibliografia = request.POST.get('bibliografia', '')
            autor.paginaweb = request.POST.get('paginaweb', '')
            autor.save()
            
            messages.success(request, 'Autor actualizado correctamente')
            return redirect('admin_autores')
        except Exception as e:
            messages.error(request, f'Error al actualizar autor: {str(e)}')
    
    return render(request, 'admin/autores/editar.html', {'autor': autor})

@login_required
@user_passes_test(es_administrador)
def eliminar_autor(request, id):
    autor = get_object_or_404(Autor, autorid=id)
    
    if request.method == 'POST':
        try:
            autor.delete()
            messages.success(request, 'Autor eliminado correctamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar autor: {str(e)}')
        return redirect('admin_autores')
    
    return render(request, 'admin/autores/eliminar.html', {'autor': autor})

# =============================================
# CRUD EDITORIALES (ADMIN) - COMPLETO
# =============================================

@login_required
@user_passes_test(es_administrador)
def admin_editoriales(request):
    editoriales = Editorial.objects.all()
    return render(request, 'admin/editoriales/listado.html', {'editoriales': editoriales})

@login_required
@user_passes_test(es_administrador)
def agregar_editorial(request):
    if request.method == 'POST':
        try:
            Editorial.objects.create(
                nombre=request.POST.get('nombre'),
                direccion=request.POST.get('direccion'),
                telefono=request.POST.get('telefono'),
                email=request.POST.get('email'),
                sitioweb=request.POST.get('sitioweb', ''),
                pais=request.POST.get('pais')
            )
            messages.success(request, 'Editorial agregada correctamente')
            return redirect('admin_editoriales')
        except Exception as e:
            messages.error(request, f'Error al agregar editorial: {str(e)}')
    
    return render(request, 'admin/editoriales/agregar.html')

@login_required
@user_passes_test(es_administrador)
def editar_editorial(request, id):
    editorial = get_object_or_404(Editorial, editorialid=id)
    
    if request.method == 'POST':
        try:
            editorial.nombre = request.POST.get('nombre')
            editorial.direccion = request.POST.get('direccion')
            editorial.telefono = request.POST.get('telefono')
            editorial.email = request.POST.get('email')
            editorial.sitioweb = request.POST.get('sitioweb', '')
            editorial.pais = request.POST.get('pais')
            editorial.save()
            
            messages.success(request, 'Editorial actualizada correctamente')
            return redirect('admin_editoriales')
        except Exception as e:
            messages.error(request, f'Error al actualizar editorial: {str(e)}')
    
    return render(request, 'admin/editoriales/editar.html', {'editorial': editorial})

@login_required
@user_passes_test(es_administrador)
def eliminar_editorial(request, id):
    editorial = get_object_or_404(Editorial, editorialid=id)
    
    if request.method == 'POST':
        try:
            editorial.delete()
            messages.success(request, 'Editorial eliminada correctamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar editorial: {str(e)}')
        return redirect('admin_editoriales')
    
    return render(request, 'admin/editoriales/eliminar.html', {'editorial': editorial})

# =============================================
# CRUD LIBROS (ADMIN) - COMPLETO
# =============================================

@login_required
@user_passes_test(es_administrador)
def admin_libros(request):
    libros = Libro.objects.all()
    
    # Calcular estadísticas
    total_stock = sum(libro.stock for libro in libros)
    valor_total = sum(libro.precioventa * libro.stock for libro in libros)
    
    return render(request, 'admin/libros/listado.html', {
        'libros': libros,
        'total_stock': total_stock,
        'valor_total': valor_total
    })
@login_required
@user_passes_test(es_administrador)
def agregar_libro(request):
    if request.method == 'POST':
        try:
            libro = Libro.objects.create(
                titulo=request.POST.get('titulo'),
                isbn=request.POST.get('isbn'),
                autorid_id=request.POST.get('autorid'),
                editorialid_id=request.POST.get('editorialid'),
                aniopublicacion=request.POST.get('aniopublicacion'),
                genero=request.POST.get('genero'),
                precioventa=request.POST.get('precioventa'),
                stock=request.POST.get('stock'),
                descripcion=request.POST.get('descripcion', '')
            )
            
            if 'portada' in request.FILES:
                libro.portada = request.FILES['portada']
                libro.save()
            
            messages.success(request, 'Libro agregado correctamente')
            return redirect('admin_libros')
        except Exception as e:
            messages.error(request, f'Error al agregar libro: {str(e)}')
    
    # OBTENER AUTORES Y EDITORIALES
    autores = Autor.objects.all()
    editoriales = Editorial.objects.all()
    
    # DEBUG: Verificar qué editoriales hay
    print("DEBUG - Editoriales disponibles:")
    for editorial in editoriales:
        print(f"  ID: {editorial.editorialid}, Nombre: {editorial.nombre}")
    
    return render(request, 'admin/libros/agregar.html', {
        'autores': autores,
        'editoriales': editoriales
    })

@login_required
@user_passes_test(es_administrador)
def editar_libro(request, id):
    libro = get_object_or_404(Libro, libroid=id)
    
    if request.method == 'POST':
        try:
            libro.titulo = request.POST.get('titulo')
            libro.isbn = request.POST.get('isbn')
            libro.autorid_id = request.POST.get('autorid')
            libro.editorialid_id = request.POST.get('editorialid')
            libro.aniopublicacion = request.POST.get('aniopublicacion')
            libro.genero = request.POST.get('genero')
            libro.precioventa = request.POST.get('precioventa')
            libro.stock = request.POST.get('stock')
            libro.descripcion = request.POST.get('descripcion', '')
            
            if 'portada' in request.FILES:
                libro.portada = request.FILES['portada']
            
            libro.save()
            messages.success(request, 'Libro actualizado correctamente')
            return redirect('admin_libros')
        except Exception as e:
            messages.error(request, f'Error al actualizar libro: {str(e)}')
    
    autores = Autor.objects.all()
    editoriales = Editorial.objects.all()
    return render(request, 'admin/libros/editar.html', {
        'libro': libro,
        'autores': autores,
        'editoriales': editoriales
    })

@login_required
@user_passes_test(es_administrador)
def eliminar_libro(request, id):
    libro = get_object_or_404(Libro, libroid=id)
    
    if request.method == 'POST':
        try:
            libro.delete()
            messages.success(request, 'Libro eliminado correctamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar libro: {str(e)}')
        return redirect('admin_libros')
    
    return render(request, 'admin/libros/eliminar.html', {'libro': libro})

# =============================================
# CRUD VENTAS (ADMIN) - COMPLETO
# =============================================

@login_required
@user_passes_test(es_administrador)
def admin_ventas(request):
    # Filtrar solo ventas con ventaid válido
    ventas = Venta.objects.exclude(ventaid__isnull=True).order_by('-fechaventa')
    return render(request, 'admin/ventas/listado.html', {'ventas': ventas})

@login_required
@user_passes_test(es_administrador)
def agregar_venta(request):
    if request.method == 'POST':
        try:
            # Validar campos requeridos
            cliente_id = request.POST.get('clienteid')
            metodopago = request.POST.get('metodopago')
            montototal_str = request.POST.get('montototal', '0')
            
            if not all([cliente_id, metodopago, montototal_str]):
                messages.error(request, 'Todos los campos marcados con * son obligatorios')
                return redirect('agregar_venta')
            
            # Validar que el cliente existe y no es staff
            if not User.objects.filter(id=cliente_id, is_staff=False).exists():
                messages.error(request, 'Cliente no válido o no encontrado')
                return redirect('agregar_venta')
            
            # Convertir valores numéricos a Decimal de forma segura
            try:
                montototal = Decimal(montototal_str) if montototal_str.strip() else Decimal('0.00')
                descuentoaplicado = Decimal(request.POST.get('descuentoaplicado', '0')) if request.POST.get('descuentoaplicado', '0').strip() else Decimal('0.00')
                pagorecibido = Decimal(request.POST.get('pagorecibido', '0')) if request.POST.get('pagorecibido', '0').strip() else Decimal('0.00')
            except (ValueError, InvalidOperation) as e:
                messages.error(request, 'Error en los valores numéricos. Use formato correcto (ej: 100.50)')
                return redirect('agregar_venta')
            
            # Validar montos negativos
            if any(val < Decimal('0.00') for val in [montototal, descuentoaplicado, pagorecibido]):
                messages.error(request, 'Los valores no pueden ser negativos')
                return redirect('agregar_venta')
            
            # Validar pago en efectivo
            if metodopago == 'EFECTIVO' and pagorecibido < montototal:
                messages.error(request, f'Para pago en efectivo, el pago recibido (${pagorecibido}) debe ser mayor o igual al total (${montototal})')
                return redirect('agregar_venta')
            
            # Crear la venta
            venta = Venta.objects.create(
                clienteid_id=cliente_id,
                metodopago=metodopago,
                montototal=montototal,
                descuentoaplicado=descuentoaplicado,
                pagorecibido=pagorecibido,
                estadoventa='COMPLETADA'
            )
            
            # Procesar libros de la venta
            libros_ids = request.POST.getlist('libros[]')
            cantidades = request.POST.getlist('cantidades[]')
            precios = request.POST.getlist('precios[]')
            
            for i, libro_id in enumerate(libros_ids):
                if libro_id and i < len(cantidades) and i < len(precios) and libro_id != '':
                    try:
                        detalle = DetalleVenta.objects.create(
                            ventaid=venta,
                            libroid_id=libro_id,
                            cantidad=int(cantidades[i]),
                            preciounitario=Decimal(precios[i]),
                            subtotal=Decimal(precios[i]) * int(cantidades[i])
                        )
                        
                        # Actualizar stock del libro
                        libro = Libro.objects.get(libroid=libro_id)
                        libro.stock -= int(cantidades[i])
                        libro.save()
                        
                    except Libro.DoesNotExist:
                        messages.warning(request, f'El libro con ID {libro_id} no existe')
                    except Exception as e:
                        messages.warning(request, f'Error al procesar libro: {str(e)}')
            
            # Calcular y guardar el cambio
            venta.calcular_cambio()
            venta.save()
            
            messages.success(request, f'Venta #{venta.ventaid} agregada correctamente')
            return redirect('admin_ventas')
            
        except Exception as e:
            messages.error(request, f'Error al agregar venta: {str(e)}')
            print(f"ERROR en agregar_venta: {e}")  # Para debugging
            
            # Recargar los libros para mostrar el formulario otra vez
            clientes = User.objects.filter(is_staff=False)
            libros = Libro.objects.filter(stock__gt=0)
            return render(request, 'admin/ventas/agregar.html', {
                'clientes': clientes,
                'libros': libros
            })
    
    # GET request - mostrar formulario
    try:
        clientes = User.objects.filter(is_staff=False)
        libros = Libro.objects.filter(stock__gt=0).select_related('autorid', 'editorialid')
        
        # Debug: Verificar qué libros hay
        print("DEBUG - Libros disponibles:")
        for libro in libros:
            print(f"  ID: {libro.libroid}, Título: {libro.titulo}, Stock: {libro.stock}, Precio: {libro.precioventa}")
        
        if not clientes.exists():
            messages.warning(request, 'No hay clientes registrados. Debes crear clientes primero.')
        
        if not libros.exists():
            messages.warning(request, 'No hay libros con stock disponible.')
        
        return render(request, 'admin/ventas/agregar.html', {
            'clientes': clientes,
            'libros': libros
        })
    
    except Exception as e:
        messages.error(request, f'Error al cargar el formulario: {str(e)}')
        return render(request, 'admin/ventas/agregar.html', {
            'clientes': [],
            'libros': []
        })
@login_required
@user_passes_test(es_administrador)
def editar_venta(request, id):
    venta = get_object_or_404(Venta, ventaid=id)
    
    if request.method == 'POST':
        try:
            venta.clienteid_id = request.POST.get('clienteid')
            venta.metodopago = request.POST.get('metodopago')
            
            # Convertir a Decimal para evitar errores
            montototal_str = request.POST.get('montototal', '0')
            descuento_str = request.POST.get('descuentoaplicado', '0')
            pagorecibido_str = request.POST.get('pagorecibido', '0')
            
            venta.montototal = Decimal(montototal_str) if montototal_str else Decimal('0.00')
            venta.descuentoaplicado = Decimal(descuento_str) if descuento_str else Decimal('0.00')
            venta.pagorecibido = Decimal(pagorecibido_str) if pagorecibido_str else Decimal('0.00')
            
            venta.estadoventa = request.POST.get('estadoventa')
            
            # Calcular cambio correctamente
            venta.calcular_cambio()
            venta.save()
            
            messages.success(request, 'Venta actualizada correctamente')
            return redirect('admin_ventas')
        except Exception as e:
            messages.error(request, f'Error al actualizar venta: {str(e)}')
            print(f"ERROR en editar_venta: {e}")  # Para debug
    
    clientes = User.objects.filter(is_staff=False)
    return render(request, 'admin/ventas/editar.html', {
        'venta': venta,
        'clientes': clientes
    })

@login_required
@user_passes_test(es_administrador)
def eliminar_venta(request, id):
    venta = get_object_or_404(Venta, ventaid=id)
    
    if request.method == 'POST':
        try:
            venta.delete()
            messages.success(request, 'Venta eliminada correctamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar venta: {str(e)}')
        return redirect('admin_ventas')
    
    return render(request, 'admin/ventas/eliminar.html', {'venta': venta})

@login_required
@user_passes_test(es_administrador)
def detalle_venta_admin(request, venta_id):
    venta = get_object_or_404(Venta, ventaid=venta_id)
    return render(request, 'admin/ventas/detalle.html', {'venta': venta})

@login_required
@user_passes_test(es_administrador)
def cancelar_venta(request, venta_id):
    venta = get_object_or_404(Venta, ventaid=venta_id)
    
    if request.method == 'POST':
        try:
            # Restaurar stock
            for detalle in venta.detalles.all():
                detalle.libroid.stock += detalle.cantidad
                detalle.libroid.save()
            
            venta.estadoventa = 'CANCELADA'
            venta.save()
            messages.success(request, 'Venta cancelada y stock restaurado')
        except Exception as e:
            messages.error(request, f'Error al cancelar venta: {str(e)}')
    
    return redirect('admin_ventas')

# =============================================
# CRUD DETALLES VENTA (ADMIN) - COMPLETO
# =============================================

@login_required
@user_passes_test(es_administrador)
def admin_detalles_venta(request):
    try:
        detalles = DetalleVenta.objects.all().select_related('ventaid', 'libroid').order_by('-ventaid_id')
        return render(request, 'admin/detalles_venta/listado.html', {'detalles': detalles})
    except Exception as e:
        messages.error(request, f'Error al cargar detalles: {str(e)}')
        return render(request, 'admin/detalles_venta/listado.html', {'detalles': []})
@login_required
@user_passes_test(es_administrador)
def agregar_detalle_venta(request):
    if request.method == 'POST':
        try:
            detalle = DetalleVenta.objects.create(
                ventaid_id=request.POST.get('ventaid'),
                libroid_id=request.POST.get('libroid'),
                cantidad=request.POST.get('cantidad'),
                preciounitario=request.POST.get('preciounitario'),
                iva=request.POST.get('iva', 0.16)
            )
            # El subtotal se calcula automáticamente en save()
            
            messages.success(request, 'Detalle de venta agregado correctamente')
            return redirect('admin_detalles_venta')
        except Exception as e:
            messages.error(request, f'Error al agregar detalle: {str(e)}')
    
    ventas = Venta.objects.all()
    libros = Libro.objects.all()
    return render(request, 'admin/detalles_venta/agregar.html', {
        'ventas': ventas,
        'libros': libros
    })

@login_required
@user_passes_test(es_administrador)
def editar_detalle_venta(request, id):
    detalle = get_object_or_404(DetalleVenta, detalleventaid=id)
    
    if request.method == 'POST':
        try:
            detalle.ventaid_id = request.POST.get('ventaid')
            detalle.libroid_id = request.POST.get('libroid')
            detalle.cantidad = request.POST.get('cantidad')
            detalle.preciounitario = request.POST.get('preciounitario')
            detalle.iva = request.POST.get('iva', 0.16)
            detalle.save()  # Esto recalcula el subtotal automáticamente
            
            messages.success(request, 'Detalle de venta actualizado correctamente')
            return redirect('admin_detalles_venta')
        except Exception as e:
            messages.error(request, f'Error al actualizar detalle: {str(e)}')
    
    ventas = Venta.objects.all()
    libros = Libro.objects.all()
    return render(request, 'admin/detalles_venta/editar.html', {
        'detalle': detalle,
        'ventas': ventas,
        'libros': libros
    })

@login_required
@user_passes_test(es_administrador)
def eliminar_detalle_venta(request, id):
    detalle = get_object_or_404(DetalleVenta, detalleventaid=id)
    
    if request.method == 'POST':
        try:
            detalle.delete()
            messages.success(request, 'Detalle de venta eliminado correctamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar detalle: {str(e)}')
        return redirect('admin_detalles_venta')
    
    return render(request, 'admin/detalles_venta/eliminar.html', {'detalle': detalle})

# =============================================
# CRUD EVENTOS (ADMIN)
# =============================================

@login_required
@user_passes_test(es_administrador)
def admin_eventos(request):
    eventos = Evento.objects.all()
    return render(request, 'admin/eventos/listado.html', {'eventos': eventos})

@login_required
@user_passes_test(es_administrador)
def agregar_evento(request):
    if request.method == 'POST':
        try:
            evento = Evento.objects.create(
                titulo=request.POST.get('titulo'),
                descripcion=request.POST.get('descripcion'),
                fecha=request.POST.get('fecha'),
                ubicacion=request.POST.get('ubicacion')
            )
            
            if 'imagen' in request.FILES:
                evento.imagen = request.FILES['imagen']
                evento.save()
            
            messages.success(request, 'Evento agregado correctamente')
            return redirect('admin_eventos')
        except Exception as e:
            messages.error(request, f'Error al agregar evento: {str(e)}')
    
    return render(request, 'admin/eventos/agregar.html')

# =============================================
# CRUD BLOG (ADMIN)
# =============================================

@login_required
@user_passes_test(es_administrador)
def admin_blog(request):
    entradas = Blog.objects.all()
    return render(request, 'admin/blog/listado.html', {'entradas': entradas})

@login_required
@user_passes_test(es_administrador)
def agregar_entrada_blog(request):
    if request.method == 'POST':
        try:
            entrada = Blog.objects.create(
                titulo=request.POST.get('titulo'),
                contenido=request.POST.get('contenido'),
                autor=request.user
            )
            
            if 'imagen' in request.FILES:
                entrada.imagen = request.FILES['imagen']
                entrada.save()
            
            messages.success(request, 'Entrada de blog agregada correctamente')
            return redirect('admin_blog')
        except Exception as e:
            messages.error(request, f'Error al agregar entrada: {str(e)}')
    
    return render(request, 'admin/blog/agregar.html')

# =============================================
# CARRITO Y COMPRAS (CLIENTE)
# =============================================

@login_required
@user_passes_test(es_cliente)
def agregar_al_carrito(request, libro_id):
    libro = get_object_or_404(Libro, libroid=libro_id)
    
    if libro.stock <= 0:
        messages.error(request, 'Este libro no está disponible en stock')
        return redirect('libros')
    
    # Verificar si el libro ya está en el carrito
    item_carrito, created = Carrito.objects.get_or_create(
        usuario=request.user,
        libro=libro,
        defaults={'cantidad': 1}
    )
    
    if not created:
        # Verificar que no exceda el stock disponible
        if item_carrito.cantidad + 1 <= libro.stock:
            item_carrito.cantidad += 1
            item_carrito.save()
            messages.success(request, f'"{libro.titulo}" agregado al carrito')
        else:
            messages.error(request, f'No hay suficiente stock de "{libro.titulo}"')
    else:
        messages.success(request, f'"{libro.titulo}" agregado al carrito')
    
    return redirect('ver_carrito')

@login_required
@user_passes_test(es_cliente)
def ver_carrito(request):
    items_carrito = Carrito.objects.filter(usuario=request.user)
    total_carrito = sum(item.subtotal() for item in items_carrito)
    
    return render(request, 'carrito/ver_carrito.html', {
        'items_carrito': items_carrito,
        'total_carrito': total_carrito
    })

@login_required
@user_passes_test(es_cliente)
def actualizar_carrito(request, item_id):
    item = get_object_or_404(Carrito, carritoid=item_id, usuario=request.user)
    
    if request.method == 'POST':
        nueva_cantidad = int(request.POST.get('cantidad', 1))
        
        if nueva_cantidad > 0 and nueva_cantidad <= item.libro.stock:
            item.cantidad = nueva_cantidad
            item.save()
            messages.success(request, 'Carrito actualizado')
        elif nueva_cantidad > item.libro.stock:
            messages.error(request, f'No hay suficiente stock. Disponible: {item.libro.stock}')
        else:
            item.delete()
            messages.success(request, 'Producto eliminado del carrito')
    
    return redirect('ver_carrito')

@login_required
@user_passes_test(es_cliente)
def eliminar_del_carrito(request, item_id):
    item = get_object_or_404(Carrito, carritoid=item_id, usuario=request.user)
    libro_titulo = item.libro.titulo
    item.delete()
    messages.success(request, f'"{libro_titulo}" eliminado del carrito')
    return redirect('ver_carrito')

@login_required
@user_passes_test(es_cliente)
def procesar_compra(request):
    if request.method == 'POST':
        try:
            items_carrito = Carrito.objects.filter(usuario=request.user)
            
            if not items_carrito:
                messages.error(request, 'Tu carrito está vacío')
                return redirect('ver_carrito')
            
            # Verificar stock disponible
            for item in items_carrito:
                if item.cantidad > item.libro.stock:
                    messages.error(request, f'No hay suficiente stock de "{item.libro.titulo}". Disponible: {item.libro.stock}')
                    return redirect('ver_carrito')
            
            # Obtener datos del formulario
            metodo_pago = request.POST.get('metodo_pago')
            if not metodo_pago:
                messages.error(request, 'Debes seleccionar un método de pago')
                return redirect('ver_carrito')
            
            # Manejar pago_recibido de forma segura
            pago_recibido_str = request.POST.get('pago_recibido', '0').strip()
            try:
                pago_recibido = Decimal(pago_recibido_str) if pago_recibido_str else Decimal('0.00')
            except:
                pago_recibido = Decimal('0.00')
            
            # Calcular total del carrito
            total_venta = Decimal('0.00')
            for item in items_carrito:
                total_venta += Decimal(str(item.libro.precioventa)) * item.cantidad
            
            # Validar pago en efectivo
            if metodo_pago == 'EFECTIVO':
                if pago_recibido <= Decimal('0.00'):
                    messages.error(request, 'Para pago en efectivo, debes ingresar la cantidad recibida')
                    return redirect('ver_carrito')
                if pago_recibido < total_venta:
                    messages.error(request, f'Pago insuficiente. Total: ${total_venta:.2f}, Recibido: ${pago_recibido:.2f}')
                    return redirect('ver_carrito')
            
            # Crear venta
            venta = Venta.objects.create(
                clienteid=request.user,
                metodopago=metodo_pago,
                pagorecibido=pago_recibido,
                montototal=total_venta,
                estadoventa='COMPLETADA'
            )
            
            # Crear detalles de venta y actualizar stock
            for item in items_carrito:
                subtotal = Decimal(str(item.libro.precioventa)) * item.cantidad
                
                DetalleVenta.objects.create(
                    ventaid=venta,
                    libroid=item.libro,
                    cantidad=item.cantidad,
                    preciounitario=item.libro.precioventa,
                    subtotal=subtotal
                )
                
                # Actualizar stock
                item.libro.stock -= item.cantidad
                item.libro.save()
            
            # Calcular y guardar cambio
            venta.calcular_cambio()
            venta.save()
            
            # Limpiar carrito
            items_carrito.delete()
            
            messages.success(request, f'¡Compra realizada exitosamente! Total: ${total_venta:.2f}')
            return redirect('detalle_venta', venta_id=venta.ventaid)
            
        except Exception as e:
            messages.error(request, f'Error al procesar la compra: {str(e)}')
            print(f"ERROR en procesar_compra: {e}")  # Debug
            return redirect('ver_carrito')
    
    return redirect('ver_carrito')

@login_required
@user_passes_test(es_cliente)
def detalle_venta(request, venta_id):
    venta = get_object_or_404(Venta, ventaid=venta_id, clienteid=request.user)
    return render(request, 'carrito/detalle_venta.html', {'venta': venta})

# =============================================
# VISTAS ADICIONALES
# =============================================

@login_required
def perfil_usuario(request):
    """Vista para que los usuarios vean y editen su perfil"""
    try:
        cliente = Cliente.objects.get(user=request.user)
    except Cliente.DoesNotExist:
        # Crear perfil si no existe
        cliente = Cliente.objects.create(user=request.user)
    
    if request.method == 'POST':
        try:
            # Actualizar usuario
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            
            # Actualizar cliente
            cliente.nombre = request.POST.get('nombre', '')
            cliente.apellido = request.POST.get('apellido', '')
            cliente.email = request.POST.get('email', '')
            cliente.telefono = request.POST.get('telefono', '')
            cliente.direccion = request.POST.get('direccion', '')
            cliente.preferenciasgenero = request.POST.get('preferenciasgenero', '')
            cliente.save()
            
            messages.success(request, 'Perfil actualizado correctamente')
        except Exception as e:
            messages.error(request, f'Error al actualizar perfil: {str(e)}')
    
    return render(request, 'perfil.html', {'cliente': cliente})

@login_required
@user_passes_test(es_cliente)
def mis_compras(request):
    """Vista para que los clientes vean su historial de compras"""
    ventas = Venta.objects.filter(clienteid=request.user).order_by('-fechaventa')
    return render(request, 'carrito/mis_compras.html', {'ventas': ventas})

