from app import create_app

# Create the application instance using the factory pattern
app = create_app()

if __name__ == '__main__':
    # You can specify the port here, or rely on the default (5000)
    app.run(debug=True, port=5005)