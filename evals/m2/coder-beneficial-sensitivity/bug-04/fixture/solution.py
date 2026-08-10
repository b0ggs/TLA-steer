def apply_operations(stock, operations):
    for op,item,qty in operations:
        stock[item]=stock.get(item,0)+qty
    return stock

