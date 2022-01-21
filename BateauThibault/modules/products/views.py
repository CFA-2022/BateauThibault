from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ProductSerializer, ProductDetailSerializer, TransactionSerializer
from .models import Product, Transaction, ImportStock
from datetime import datetime, timedelta
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated

class ProductListAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        return queryset

    def get(self, request, *args, **kwargs):
        products = self.get_queryset()
        serializer = ProductSerializer(products, many=True)

        return Response(serializer.data)

class ProductRetrieveAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ProductDetailSerializer

    def get(self, request, id, *args, **kwargs):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if id != None:
            serializer = ProductSerializer(product)
            return Response(serializer.data)

class ProductUpdateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get_object(self, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Http404

    def save_transaction(self, product, quantityRetrait):
        transaction = Transaction()
        transaction.product = product
        transaction.selling_date = str(datetime.now())
        transaction.selling_quantity = quantityRetrait
        if product.sale is True:
            transaction.amount_total = quantityRetrait * product.price_on_sale
        else:
            transaction.amount_total = quantityRetrait * product.price_selling
        transaction.save()

    def save_stock(self, product, quantityImport):
        stock = ImportStock()
        stock.product = product
        stock.import_date = str(datetime.now())
        stock.import_quantity = quantityImport
        stock.amount_spending = quantityImport * product.price
        stock.save()

    def put(self, request, *args, **kwargs):
        try:
            products = []
            if request.method == "PUT" and request.data:
                for prod in request.data:
                    product = self.get_object(prod["id"])
                    quantityInStock = product.quantity_in_stock

                    for key, val in prod.items():
                        if key == "discount":
                            if prod[key] == 0:
                                product.sale = False
                            else:
                                product.sale = True
                            product.discount = val
                            sale = val/100 * product.price_selling
                            product.price_on_sale = product.price_selling - sale
                        if key in product.__dict__:
                            product.__dict__[key] = val

                    if product.quantity_in_stock < quantityInStock:
                        quantityRetrait = quantityInStock - product.quantity_in_stock
                        self.save_transaction(product, float(quantityRetrait))
                    else:
                        quantityImport = product.quantity_in_stock - quantityInStock
                        self.save_stock(product, float(quantityImport))

                    product.save()
                    products.append(product)
            serializer = ProductSerializer(products, many=True)
        except UnboundLocalError as e:
            print(e)
            print("Can't find any product")

        return Response(serializer.data)


class TransactionRetrieveAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def parse_queryset(self, queryset, dataList, typeData, start):
        sum = 0
        quantity = 0
        dataDict = {}
        if queryset:
            if typeData == "day":
                dataDict[typeData] = start.date()
            else:
                dataDict[typeData] = start
            for query in queryset:
                sum += query.amount_total
                quantity += query.selling_quantity
            dataDict["income"] = sum
            dataDict["selling_quantity"] = quantity
            dataList.append(dataDict)
        return dataList

    def get_data_by_days(self):
        dataList = []

        start = self.request.query_params.get('start_date')
        start = datetime.strptime(start + ' 00:00:00', '%Y-%m-%d %H:%M:%S')

        end = self.request.query_params.get('end_date')
        end = datetime.strptime(end + ' 00:00:00', '%Y-%m-%d %H:%M:%S')

        delta = timedelta(days=1)

        while start < end:
            endOfDay = start.replace(hour=23, minute=59, second=59)
            queryset = Transaction.objects.filter(selling_date__range=[start, endOfDay])
            dataList = self.parse_queryset(queryset, dataList, "day", start)
            start += delta
        return dataList

    def get_data_by_week(self):
        dataList = []
        start = int(self.request.query_params.get('start_date'))
        end = int(self.request.query_params.get('end_date'))
        year = int(self.request.query_params.get('year'))
        while start < end:
            queryset = Transaction.objects.filter(selling_date__week=start, selling_date__year=year)
            dataList = self.parse_queryset(queryset, dataList, "week", start)
            start += 1
        return dataList

    def get_data_by_month(self):
        dataList = []
        start = int(self.request.query_params.get('start_date'))
        end = int(self.request.query_params.get('end_date'))
        year = int(self.request.query_params.get('year'))
        while start < end:
            queryset = Transaction.objects.filter(selling_date__month=start, selling_date__year=year)
            dataList = self.parse_queryset(queryset, dataList, "month", start)
            start += 1
        return dataList

    def get_data_by_trimestre(self):
        dataList = []
        start = int(self.request.query_params.get('start_date'))
        end = int(self.request.query_params.get('end_date'))
        year = int(self.request.query_params.get('year'))
        while start < end:
            queryset = Transaction.objects.filter(selling_date__quarter=start, selling_date__year=year)
            dataList = self.parse_queryset(queryset, dataList, "trimestre", start)
            start += 1
        return dataList

    def get_data_by_year(self):
        dataList = []
        start = int(self.request.query_params.get('start_date'))
        end = int(self.request.query_params.get('end_date'))
        while start < end:
            queryset = Transaction.objects.filter(selling_date__year=start)
            dataList = self.parse_queryset(queryset, dataList, "year", start)
            start += 1
        return dataList

    def get_queryset(self):
        typeData = self.request.query_params.get('type')

        if typeData == "day":
            dataList = self.get_data_by_days()
        elif typeData == "week":
            dataList = self.get_data_by_week()
        elif typeData == "month":
            dataList = self.get_data_by_month()
        elif typeData == "year":
            dataList = self.get_data_by_year()
        elif typeData == "trimestre":
            dataList = self.get_data_by_trimestre()

        return dataList

    def get(self, request, *args, **kwargs):
        try:
            dataList = self.get_queryset()
        except UnboundLocalError as e:
            print(e)
            print("Something broken")
        return Response(dataList)

class StatisticRetrieveAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        start = int(self.request.query_params.get('year_start'))
        end = int(self.request.query_params.get('year_end'))
        dataList = []
        while start < end:
            selling_sum = 0
            depending_sum = 0
            dataDict = {}
            queryTrans = Transaction.objects.filter(selling_date__year=start)
            queryImport = ImportStock.objects.filter(import_date__year=start)
            for trans in queryTrans:
                selling_sum += trans.amount_total
            for imp in queryImport:
                depending_sum += imp.amount_spending
            start += 1
            tax = round(0.3 * selling_sum, 2)
            benefice = round(selling_sum - depending_sum - tax, 2)
            dataDict = {
                "year": start,
                "selling_sum": selling_sum,
                "depending_sum": depending_sum,
                "tax": tax,
                "benefice": benefice
            }
            dataList.append(dataDict)
        return dataList

    def get(self, request, *args, **kwargs):
        try:
            dataList = self.get_queryset()
            print(dataList)
        except UnboundLocalError as e:
            print(e)
            print("Something broken")
        return Response(dataList)
