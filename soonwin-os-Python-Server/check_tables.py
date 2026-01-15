from app import create_app

app = create_app()
with app.app_context():
    from app.models.order import Order
    print('Order table name:', Order.__tablename__)
    
    from app.models.expense import AnnualTarget, IndividualExpense
    print('AnnualTarget table name:', AnnualTarget.__tablename__)
    print('IndividualExpense table name:', IndividualExpense.__tablename__)