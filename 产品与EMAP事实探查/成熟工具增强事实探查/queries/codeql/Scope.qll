import cpp

/** Replace the two scopes with this database's actual source paths.
 * Keep targets/configurations separate. The runner rejects untouched placeholders.
 */
predicate inScope(File f) {
  f.getAbsolutePath().matches("%/__SET_PRODUCT_SCOPE__/%")
  or
  f.getAbsolutePath().matches("%/__SET_EMAP_SCOPE__/%")
}
