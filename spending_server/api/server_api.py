from django.core import serializers
from django.http import HttpResponseBadRequest
from django.shortcuts import render

import modules.network.fns_api.query as fns
from app.check.forms import FiscalData
from app.check.models import Check, Item
from modules.parsers import json_parser


def get_check(request):
    """ API Method to get check. Credentials required.

    """
    if request.method == "POST":
        fiscalDocumentNumber = request.POST.get("id")
        if not len(fiscalDocumentNumber) or not fiscalDocumentNumber.isdigit():
            return HttpResponseBadRequest("wrong check id")

        try:
            fiscalDocumentNumber = int(fiscalDocumentNumber)
        except ValueError:
            return HttpResponseBadRequest("wrong check id")
        check = Check.objects.get(fiscalDocumentNumber=fiscalDocumentNumber)
        goods = Item.objects.filter(cash_check=check)
        categories = {}
        for good in goods:
            if good.category.name in categories:
                categories[good.category.name] += (good.sum / check.totalSum) * 100
            else:
                categories[good.category.name] = (good.sum / check.totalSum) * 100
        context = {
            "check": check,
            "goods": goods,
            "categories": categories
        }
        return render(request, "cash_chart.html", context=context)


def add_check(request):
    if request.method == "POST":
        form = FiscalData(request.POST)
        if not form.is_valid():
            return HttpResponseBadRequest("wrong check data")
        fn = request.POST.get("fn")
        fiscalDocumentNumber = request.POST.get("fd")
        fpd = request.POST.get("fpd")
        json = fns.get_check("+", "", fn, fiscalDocumentNumber, fpd)
        parser = json_parser.JsonParser(json=json, models=(Check, Item))
        serialized_check = parser.json_to_database()
        check_object = None
        for deserialized_object in serializers.deserialize("python", serialized_check):
            if deserialized_object.object._meta.model_name == 'check':
                check_object = deserialized_object.object
            elif deserialized_object.object._meta.model_name == 'item':
                deserialized_object.object.cash_check = check_object
            deserialized_object.save()
        return render(request, "check.html")
