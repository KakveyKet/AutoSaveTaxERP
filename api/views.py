import pandas as pd
import shutil
import os
import zipfile
import mimetypes
from django.http import HttpResponse
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import viewsets, permissions, filters, generics, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser 
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView 

from .models import User, Forwarder, Destination, OrderImport
from .serializers import (
    UserSerializer, RegisterSerializer, ForwarderSerializer, 
    DestinationSerializer, OrderImportSerializer, MyTokenObtainPairSerializer
)
from .bot import AutoDownloadBot

class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class IsAdminOrSelf(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.role == 'admin':
            return True
        return obj.id == request.user.id
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    

# --- 1. SECRET RECOVERY VIEW (NEW) ---
class SecretAdminRecoveryView(APIView):
    permission_classes = [AllowAny] # Public, but protected by secret key

    def post(self, request):
        secret_key = request.data.get('secret_key')
        username = request.data.get('username')
        password = request.data.get('password')

        # SECURITY: This is your "Master Key". Change this to something complex!
        if secret_key != "admin-rescue-999": 
            return Response({'error': 'Invalid Secret Key. Access Denied.'}, status=403)

        if not username or not password:
            return Response({'error': 'Username and Password required.'}, status=400)

        try:
            # Case 1: User exists -> Reset Password
            user = User.objects.get(username=username)
            user.set_password(password)
            user.role = 'admin' # Force upgrade to admin
            user.is_superuser = True
            user.is_staff = True
            user.save()
            return Response({'message': f'Successfully reset password for {username}. You can now login.'})
        
        except User.DoesNotExist:
            # Case 2: User does not exist -> Create New Admin
            try:
                User.objects.create_superuser(
                    username=username, 
                    email=f"{username}@gmail.com", # Placeholder email if not provided
                    password=password, 
                    role='admin'
                )
                return Response({'message': f'New Admin user {username} created successfully.'})
            except Exception as e:
                return Response({'error': str(e)}, status=400)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSelf] 
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'role']
    def get_queryset(self):
        queryset = User.objects.all().order_by('-created_at')
        if self.action == 'list': return queryset.exclude(id=self.request.user.id)
        return queryset

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class ForwarderViewSet(viewsets.ModelViewSet):
    queryset = Forwarder.objects.all().order_by('-created_at')
    serializer_class = ForwarderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'status']
    def perform_create(self, serializer): serializer.save(created_by=self.request.user)

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all().order_by('-created_at')
    serializer_class = DestinationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'status']
    def perform_create(self, serializer): serializer.save(created_by=self.request.user)

# class OrderImportViewSet(viewsets.ModelViewSet):
#     serializer_class = OrderImportSerializer
#     permission_classes = [IsAuthenticated]
#     pagination_class = StandardPagination
#     parser_classes = (MultiPartParser, FormParser, JSONParser)
#     filter_backends = [filters.SearchFilter]
#     search_fields = ['file', 'uploaded_by__username']

#     def get_queryset(self):
#         queryset = OrderImport.objects.all().order_by('-uploaded_at')
        
#         # Date Filtering logic
#         period = self.request.query_params.get('period')
#         now = timezone.now()
        
#         if period == 'daily':
#             # Files uploaded today (since midnight)
#             start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
#             queryset = queryset.filter(uploaded_at__gte=start_date)
#         elif period == 'weekly':
#             # Last 7 days
#             start_date = now - timedelta(days=7)
#             queryset = queryset.filter(uploaded_at__gte=start_date)
#         elif period == 'monthly':
#             # Last 30 days
#             start_date = now - timedelta(days=30)
#             queryset = queryset.filter(uploaded_at__gte=start_date)
            
#         return queryset

#     def perform_create(self, serializer):
#         instance = serializer.save(uploaded_by=self.request.user)
#         self.process_file(instance)

#     def perform_destroy(self, instance):
#         if instance.file: instance.file.delete(save=False)
#         if instance.generated_zip: instance.generated_zip.delete(save=False)
#         temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp', str(instance.id))
#         if os.path.exists(temp_dir):
#             try: shutil.rmtree(temp_dir)
#             except Exception as e: print(f"Error deleting temp: {e}")
#         instance.delete()

#     def process_file(self, instance):
#         try:
#             file_path = instance.file.path
#             df_preview = pd.read_excel(file_path, header=None, nrows=20)
#             header_row_index = -1
#             for i, row in df_preview.iterrows():
#                 row_str = row.astype(str).str.cat(sep=' ')
#                 if "INVOICE NUMBER" in row_str:
#                     header_row_index = i
#                     break
#             if header_row_index == -1:
#                 instance.parsed_data = {"error": "Could not find 'INVOICE NUMBER' header."}
#                 instance.save()
#                 return
#             df = pd.read_excel(file_path, header=header_row_index)
#             valid_rows = df[df['INVOICE NUMBER'].notna()]
#             extracted_data = []
#             for _, row in valid_rows.iterrows():
#                 def clean(val):
#                     if pd.isna(val): return ""
#                     if isinstance(val, datetime): return val.strftime('%Y-%m-%d')
#                     return str(val).strip()
#                 item = {
#                     "no": clean(row.get('No.')),
#                     "customer": clean(row.get('customer')),
#                     "invoice_number": clean(row.get('INVOICE NUMBER')),
#                     "destination": clean(row.get('DESTINATION')),
#                     "forwarder": clean(row.get('FORWARDER')),
#                     "qty": row.get('QTY PCS', 0) if pd.notna(row.get('QTY PCS')) else 0,
#                     "amount": row.get('AMOUNT INV (USD)', 0) if pd.notna(row.get('AMOUNT INV (USD)')) else 0,
#                     "eta": clean(row.get('ETA')),
#                     "via": clean(row.get('VIA'))
#                 }
#                 extracted_data.append(item)
#             instance.parsed_data = extracted_data
#             instance.save()
#         except Exception as e:
#             instance.parsed_data = {"error": str(e)}
#             instance.save()

#     @action(detail=True, methods=['post'])
#     def run_bot(self, request, pk=None):
#         order = self.get_object()
#         order.bot_status = 'running'
#         order.save()
#         config = request.data
#         bot = AutoDownloadBot(order, config)
#         bot.run()
#         return Response({'message': 'Bot started.'})

#     @action(detail=True, methods=['post'])
#     def stop_bot(self, request, pk=None):
#         order = self.get_object()
#         order.bot_status = 'stopping'
#         order.save()
#         return Response({'message': 'Stop signal sent.'})

#     @action(detail=True, methods=['get'], url_path='preview/(?P<invoice_number>[^/.]+)')
#     def preview_file(self, request, pk=None, invoice_number=None):
#         order = self.get_object()
#         if not order.generated_zip:
#             return Response({'error': 'No zip file available.'}, status=404)
#         try:
#             with zipfile.ZipFile(order.generated_zip.path, 'r') as zip_ref:
#                 matching_files = [f for f in zip_ref.namelist() if f.startswith(invoice_number)]
#                 if not matching_files:
#                     return Response({'error': 'File not found.'}, status=404)
#                 filename = matching_files[0]
#                 file_content = zip_ref.read(filename)
#                 content_type, _ = mimetypes.guess_type(filename)
#                 if not content_type: content_type = 'application/octet-stream'
#                 response = HttpResponse(file_content, content_type=content_type)
#                 response['Content-Disposition'] = f'inline; filename="{filename}"'
#                 return response
#         except Exception as e:
#             return Response({'error': str(e)}, status=500)

#     # --- NEW: Aggregated Stats Action ---
#     @action(detail=False, methods=['get'])
#     def report_stats(self, request):
#         """
#         Returns aggregated download stats based on 'period' filter.
#         """
#         queryset = self.get_queryset() # Uses the same date filter logic as the list
        
#         total_files = 0
#         total_invoices = 0
#         total_downloaded = 0
        
#         # Iterate to sum up JSON data (Doing this in Python as JSON aggregation in SQLite is limited)
#         for order in queryset:
#             total_files += 1
#             if order.parsed_data and isinstance(order.parsed_data, list):
#                 total_invoices += len(order.parsed_data)
#                 # Count items with status='completed'
#                 downloaded = sum(1 for item in order.parsed_data if item.get('status') == 'completed')
#                 total_downloaded += downloaded

#         return Response({
#             'total_files': total_files,
#             'total_invoices': total_invoices,
#             'total_downloaded': total_downloaded,
#             'success_rate': round((total_downloaded / total_invoices * 100) if total_invoices > 0 else 0, 1)
#         })

# class SystemSettingView(APIView):
#     permission_classes = [IsAuthenticated]
#     def get(self, request):
#         setting, created = SystemSetting.objects.get_or_create(id=1)
#         serializer = SystemSettingSerializer(setting)
#         return Response(serializer.data)
#     def put(self, request):
#         setting, created = SystemSetting.objects.get_or_create(id=1)
#         serializer = SystemSettingSerializer(setting, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderImportViewSet(viewsets.ModelViewSet):
    serializer_class = OrderImportSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = [filters.SearchFilter]
    search_fields = ['file', 'uploaded_by__username']

    def get_queryset(self):
        queryset = OrderImport.objects.all().order_by('-uploaded_at')
        
        # Date Filtering logic
        period = self.request.query_params.get('period')
        now = timezone.now()
        
        if period == 'daily':
            # Files uploaded today (since midnight)
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            queryset = queryset.filter(uploaded_at__gte=start_date)
        elif period == 'weekly':
            # Last 7 days
            start_date = now - timedelta(days=7)
            queryset = queryset.filter(uploaded_at__gte=start_date)
        elif period == 'monthly':
            # Last 30 days
            start_date = now - timedelta(days=30)
            queryset = queryset.filter(uploaded_at__gte=start_date)
            
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save(uploaded_by=self.request.user)
        self.process_file(instance)

    def perform_destroy(self, instance):
        if instance.file: instance.file.delete(save=False)
        if instance.generated_zip: instance.generated_zip.delete(save=False)
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp', str(instance.id))
        if os.path.exists(temp_dir):
            try: shutil.rmtree(temp_dir)
            except Exception as e: print(f"Error deleting temp: {e}")
        instance.delete()

    def process_file(self, instance):
        try:
            file_path = instance.file.path
            df_preview = pd.read_excel(file_path, header=None, nrows=20)
            header_row_index = -1
            for i, row in df_preview.iterrows():
                row_str = row.astype(str).str.cat(sep=' ')
                if "INVOICE NUMBER" in row_str:
                    header_row_index = i
                    break
            if header_row_index == -1:
                instance.parsed_data = {"error": "Could not find 'INVOICE NUMBER' header."}
                instance.save()
                return
            df = pd.read_excel(file_path, header=header_row_index)
            valid_rows = df[df['INVOICE NUMBER'].notna()]
            extracted_data = []
            for _, row in valid_rows.iterrows():
                def clean(val):
                    if pd.isna(val): return ""
                    if isinstance(val, datetime): return val.strftime('%Y-%m-%d')
                    return str(val).strip()
                
                inv_num = clean(row.get('INVOICE NUMBER'))
                
                # --- FILTER LOGIC: Skip if hyphen exists ---
                if '-' in inv_num:
                    continue
                # -------------------------------------------

                item = {
                    "no": clean(row.get('No.')),
                    "customer": clean(row.get('customer')),
                    "invoice_number": inv_num,
                    "destination": clean(row.get('DESTINATION')),
                    "forwarder": clean(row.get('FORWARDER')),
                    "qty": row.get('QTY PCS', 0) if pd.notna(row.get('QTY PCS')) else 0,
                    "amount": row.get('AMOUNT INV (USD)', 0) if pd.notna(row.get('AMOUNT INV (USD)')) else 0,
                    "eta": clean(row.get('ETA')),
                    "via": clean(row.get('VIA'))
                }
                extracted_data.append(item)
            instance.parsed_data = extracted_data
            instance.save()
        except Exception as e:
            instance.parsed_data = {"error": str(e)}
            instance.save()

    @action(detail=True, methods=['post'])
    def run_bot(self, request, pk=None):
        order = self.get_object()
        order.bot_status = 'running'
        order.save()
        config = request.data
        bot = AutoDownloadBot(order, config)
        bot.run()
        return Response({'message': 'Bot started.'})

    @action(detail=True, methods=['post'])
    def stop_bot(self, request, pk=None):
        order = self.get_object()
        order.bot_status = 'stopping'
        order.save()
        return Response({'message': 'Stop signal sent.'})

    @action(detail=True, methods=['get'], url_path='preview/(?P<invoice_number>[^/.]+)')
    def preview_file(self, request, pk=None, invoice_number=None):
        order = self.get_object()
        if not order.generated_zip:
            return Response({'error': 'No zip file available.'}, status=404)
        try:
            with zipfile.ZipFile(order.generated_zip.path, 'r') as zip_ref:
                matching_files = [f for f in zip_ref.namelist() if f.startswith(invoice_number)]
                if not matching_files:
                    return Response({'error': 'File not found.'}, status=404)
                filename = matching_files[0]
                file_content = zip_ref.read(filename)
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type: content_type = 'application/octet-stream'
                response = HttpResponse(file_content, content_type=content_type)
                response['Content-Disposition'] = f'inline; filename="{filename}"'
                return response
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    # --- NEW: Aggregated Stats Action ---
    @action(detail=False, methods=['get'])
    def report_stats(self, request):
        """
        Returns aggregated download stats based on 'period' filter.
        """
        queryset = self.get_queryset() # Uses the same date filter logic as the list
        
        total_files = 0
        total_invoices = 0
        total_downloaded = 0
        
        # Iterate to sum up JSON data (Doing this in Python as JSON aggregation in SQLite is limited)
        for order in queryset:
            total_files += 1
            if order.parsed_data and isinstance(order.parsed_data, list):
                total_invoices += len(order.parsed_data)
                # Count items with status='completed'
                downloaded = sum(1 for item in order.parsed_data if item.get('status') == 'completed')
                total_downloaded += downloaded

        return Response({
            'total_files': total_files,
            'total_invoices': total_invoices,
            'total_downloaded': total_downloaded,
            'success_rate': round((total_downloaded / total_invoices * 100) if total_invoices > 0 else 0, 1)
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    try:
        user_count = User.objects.count()
        forwarder_count = Forwarder.objects.count()
        destination_count = Destination.objects.count()
        order_count = OrderImport.objects.count()
        recent_uploads = OrderImport.objects.order_by('-uploaded_at')[:50].values('id', 'file', 'uploaded_at', 'uploaded_by__username')
        return Response({
            'total_users': user_count,
            'total_forwarders': forwarder_count,
            'total_destinations': destination_count,
            'total_orders': order_count,
            'recent_uploads': list(recent_uploads)
        })
    except Exception as e: return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def say_hello(request): return Response({'message': f'Hello, {request.user.username}!'})


