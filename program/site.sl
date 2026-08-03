# Define your site below.
# Run the compiler and it will generate HTML, create a GitHub repo, and deploy to Vercel.
#
# NOTE: replace TU_CORREO_AQUI with a real e-mail before the final demo.

site "javier-valladares-sitelang-lab3" {
  title       = "Javier Valladares — UVG 2026"
  description = "Compilador con ANTLR que genera y despliega un sitio estatico"
  theme       = "dark"

  page "index" {
    hero    = "Hola, este sitio lo construyo y desplego un compilador que escribi"
    about   = "Soy estudiante de la Universidad del Valle de Guatemala, en el curso de Construccion de Compiladores 2026. Esta pagina se genero a partir de un DSL propio (SiteLang), se subio a GitHub y se desplego en Vercel, todo por mi compilador de ANTLR."
    contact = "TU_CORREO_AQUI"
  }
}
