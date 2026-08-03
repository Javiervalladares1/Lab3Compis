# Syntactically valid but uses an unsupported theme -> semantic error.
site "bad-theme-site" {
  title = "Bad Theme"
  theme = "blue"

  page "index" {
    hero = "The theme blue is not allowed"
  }
}
