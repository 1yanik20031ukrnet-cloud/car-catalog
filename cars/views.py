from django.shortcuts import render


def catalog(request):
    """Main page: dealer header + car catalog (cars will appear in stage 2-3)."""
    return render(request, 'cars/catalog.html')
