from django import forms

class CuadroForm(forms.Form):
    titulo = forms.CharField(label="Nombre del cuadro")
    pass
class AutorForm(forms.Form):
    autor = forms.CharField(label="Nombre del autor")
    pass
class DescripcionForm(forms.Form):
    descripcion = forms.CharField(label="Busqueda en la descripcion")
    pass