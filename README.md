## **Books Integration**

_📢 Undergoing Alpha Testing. Please open an issue if you encounter any bugs._

Frappe Books Integration for ERPNext

## Installation

### Manual Installation

Once you've [set up a Frappe site](https://frappeframework.com/docs/v14/user/en/installation/), installing Books Integration is simple.

1. Download the App using the Bench CLI

   ```sh
   bench get-app https://github.com/wahni-green/books_integration --branch version-15
   ```

1. Install the App on your site

   ```sh
   bench --site [site name] install-app books_integration
   ```

### Configuration

You can configure the following options via Books Sync Settings Doctype.

- **Enable Sync**: to toggle the Sync functionality.
- **Sync Interval**: to set how often the Sync should perform in milliseconds.

    <details>
    <summary><code>Item</code></summary>

    <h4>Item Tax Template Map</h4>
    You can set the Tax Templates you use in ERPNext and their equivalents that you want to use in Books.

</details>

#### License

mit
