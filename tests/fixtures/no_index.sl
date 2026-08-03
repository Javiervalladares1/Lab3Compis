# Syntactically valid but has no "index" page -> semantic error.
site "no-index-site" {
  title = "No Index"
  theme = "dark"

  page "home" {
    hero = "This is not called index"
  }
}
