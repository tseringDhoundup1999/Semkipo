
class GeneralMessages:
    # general messages
    SERVER_ERROR_MESSAGE = "Something went wrong on the server. please try again later."
    VALIDATION_ERROR_MESSAGE = "Validation failed. Please check the input data and try again."
    DOES_NOT_EXIST_MESSAGE = "The requested resource does not exist."
    
    # Just Get API message
    GET_SUCCESS_MESSAGE = "Data retrieved successfully."

class SuccessMessages:
    # accounts success messages
    LOGIN_SUCCESS_MESSAGE = "Login successful! Welcome back."
    
    # customers success messages
    CUSTOMER_CREATED_MESSAGE = "Customer has been created successfully."
    CUSTOMER_ALREADY_EXISTS = "Customer already exists. Returning existing customer details."
    CUSTOMER_UPDATE_NAME = "Customer name has been updated successfully."
    
    
    # measurement success messages
    MEASUREMENT_TYPE_CREATED = "Measurement type has been created successfully."
    ITEM_TYPE_CREATED = "Measurement item type has been created successfully."
    MEASUREMENT_DELETED = "Measurement type deleted successfully."
    MEASUREMENT_ITEM_TYPE_DELETED = "Measurement item type has been deleted successfully."
    

class ErrorMessages:
    # accounts error messages
    EMAIL_NOT_VERIFIED_MESSAGE = "Please verify your email before logging in."
    
    # customers error messages 
    CUSTOMER_DOES_NOT_EXIST = "Customer with the provided contact does not exist."
    
    # measurement error messages
    MEASUREMENT_ALREADY_EXISTS = "Measurement type with the same name already exists."
    ITEM_TYPE_ALREADY_EXISTS = "Item type with the same name already exists."
    MEASUREMENT_DOES_NOT_EXIST = "Measurement type with the provided id does not exist."
    MEASUREMENT_ITEM_TYPE_DOES_NOT_EXIST = "Measurement item type with the provided id does not exist."