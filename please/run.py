from app import create_app

# create the application instance 
app = create_app()

if __name__ == '__main__':
    # change port here if needed
    app.run(debug=True, port=5005)
