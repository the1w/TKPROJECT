# NFC Tag Manager

NFC Tag Manager is a web application that allows users to manage their NFC tags and control where they redirect. Users can create accounts, add NFC tags, and update the redirect URLs associated with each tag.

## Features

- User registration and authentication
- Dashboard for managing NFC tags
- Add, update, and delete NFC tags
- Redirect functionality for NFC tags
- QR code generation for each NFC tag
- Password reset functionality
- Multi-language support (English and Lithuanian)
- Error handling for 404, 403, and 500 errors

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/nfc-tag-manager.git
   cd nfc-tag-manager
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```
   python
   >>> from app import app, db
   >>> with app.app_context():
   ...     db.create_all()
   >>> exit()
   ```

5. Compile translations:
   ```
   pybabel compile -d translations
   ```

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open a web browser and navigate to `http://127.0.0.1:5000`.

3. Register a new account or log in with an existing account.

4. Use the dashboard to manage your NFC tags:
   - Add new NFC tags by providing a unique Tag ID and a redirect URL.
   - Update existing NFC tags by modifying the redirect URL.
   - Delete NFC tags you no longer need.
   - View QR codes for each NFC tag.

5. To use an NFC tag, access the URL `http://127.0.0.1:5000/redirect/<tag_id>`, replacing `<tag_id>` with the actual Tag ID. This will redirect to the associated URL.

6. To reset your password, click on the "Forgot Password?" link on the login page and follow the instructions.

7. To change the language, use the language selector in the header.

## Development

- The main application logic is in `app.py`.
- HTML templates are located in the `templates` directory.
- Static files (CSS, JavaScript) are in the `static` directory.
- Translations are in the `translations` directory.

To add or update translations:

1. Extract messages:
   ```
   pybabel extract -F babel.cfg -o messages.pot .
   ```

2. Update translations:
   ```
   pybabel update -i messages.pot -d translations
   ```

3. Translate the messages in `translations/lt/LC_MESSAGES/messages.po`.

4. Compile translations:
   ```
   pybabel compile -d translations
   ```

## Security Considerations

- Always use HTTPS in a production environment.
- Implement rate limiting to prevent abuse of the redirect functionality.
- Regularly update dependencies to patch any security vulnerabilities.
- Use environment variables for sensitive information like secret keys and database credentials.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.