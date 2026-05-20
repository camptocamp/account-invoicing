This module allows fixed-amount taxes to have their amount expressed in a
specific currency instead of the document currency.

When a currency is set on the tax, the fixed amount is automatically
converted to the document currency at invoice time using the appropriate
exchange rate.

Three conversion scenarios are supported:

- **Tax currency = document currency**: no conversion is applied.
- **Tax currency = company currency**: the amount is converted using the
  document's exchange rate.
- **Tax currency is a third currency**: the amount is first converted to the
  company currency, then to the document currency.

The conversion rate is determined at the invoice date, not the current date,
ensuring accurate historical conversions.
