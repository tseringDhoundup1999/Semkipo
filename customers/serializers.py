from rest_framework import serializers
import re 

class contactSerializers(serializers.Serializer):
    contact = serializers.CharField(min_length=7,max_length=10)
    
    # custom validation 
    def validate_contact(self,value):
        value = value.replace('-','').strip()
        
        # Mobile: 98xxxxxx or 97xxxxxx
        mobile_patterns = r"^(98|97)\d{8}$"
        
        # Landline:0xxxxx (7-10 digits total)
        
        landline_pattern = r"^0\d{6,9}$"
        
        if re.match(mobile_patterns,value) or re.match(landline_pattern,value):
            return value 
        raise serializers.ValidationError("Invalid phone number.")
    