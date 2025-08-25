"""Form validation and handling utility functions."""

import re
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime

import streamlit as st

# Import logger for error handling
from app.utils.logger import app_logger


class FormValidator:
    """Form validation utility class."""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email address format."""
        if not email:
            return False, "Email is required"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        
        return True, ""
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """Validate URL format."""
        if not url:
            return False, "URL is required"
        
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url, re.IGNORECASE):
            return False, "Invalid URL format (must start with http:// or https://)"
        
        return True, ""
    
    @staticmethod
    def validate_session_id(session_id: str) -> Tuple[bool, str]:
        """Validate session ID format (UUID)."""
        if not session_id:
            return False, "Session ID is required"
        
        # UUID pattern (with or without hyphens)
        uuid_pattern = r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$'
        if not re.match(uuid_pattern, session_id.replace('-', ''), re.IGNORECASE):
            return False, "Invalid session ID format (must be a valid UUID)"
        
        return True, ""
    
    @staticmethod
    def validate_text_length(text: str, min_length: int = 0, max_length: int = 10000) -> Tuple[bool, str]:
        """Validate text length."""
        if not text and min_length > 0:
            return False, f"Text is required (minimum {min_length} characters)"
        
        if len(text) < min_length:
            return False, f"Text must be at least {min_length} characters long"
        
        if len(text) > max_length:
            return False, f"Text must be no more than {max_length} characters long"
        
        return True, ""
    
    @staticmethod
    def validate_required_field(value: Any, field_name: str) -> Tuple[bool, str]:
        """Validate that a required field has a value."""
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, f"{field_name} is required"
        
        return True, ""
    
    @staticmethod
    def validate_numeric_range(value: Union[int, float], min_val: Optional[float] = None, max_val: Optional[float] = None) -> Tuple[bool, str]:
        """Validate numeric value is within range."""
        if min_val is not None and value < min_val:
            return False, f"Value must be at least {min_val}"
        
        if max_val is not None and value > max_val:
            return False, f"Value must be no more than {max_val}"
        
        return True, ""
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: List[str]) -> Tuple[bool, str]:
        """Validate file type based on extension."""
        if not filename:
            return False, "Filename is required"
        
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if file_ext not in [ext.lower() for ext in allowed_types]:
            return False, f"File type must be one of: {', '.join(allowed_types)}"
        
        return True, ""


class FormBuilder:
    """Form building utility class."""
    
    def __init__(self, form_key: str):
        self.form_key = form_key
        self.fields = {}
        self.validators = {}
        self.errors = {}
    
    def add_text_input(self, key: str, label: str, placeholder: str = "", help_text: str = "", 
                      required: bool = False, min_length: int = 0, max_length: int = 10000) -> 'FormBuilder':
        """Add text input field."""
        self.fields[key] = {
            'type': 'text_input',
            'label': label,
            'placeholder': placeholder,
            'help': help_text,
            'required': required
        }
        
        # Add validators
        validators = []
        if required:
            validators.append(lambda v: FormValidator.validate_required_field(v, label))
        if min_length > 0 or max_length < 10000:
            validators.append(lambda v: FormValidator.validate_text_length(v, min_length, max_length))
        
        self.validators[key] = validators
        return self
    
    def add_text_area(self, key: str, label: str, placeholder: str = "", help_text: str = "", 
                     required: bool = False, min_length: int = 0, max_length: int = 10000, height: int = 100) -> 'FormBuilder':
        """Add text area field."""
        self.fields[key] = {
            'type': 'text_area',
            'label': label,
            'placeholder': placeholder,
            'help': help_text,
            'required': required,
            'height': height
        }
        
        # Add validators
        validators = []
        if required:
            validators.append(lambda v: FormValidator.validate_required_field(v, label))
        if min_length > 0 or max_length < 10000:
            validators.append(lambda v: FormValidator.validate_text_length(v, min_length, max_length))
        
        self.validators[key] = validators
        return self
    
    def add_selectbox(self, key: str, label: str, options: List[str], help_text: str = "", 
                     required: bool = False) -> 'FormBuilder':
        """Add selectbox field."""
        self.fields[key] = {
            'type': 'selectbox',
            'label': label,
            'options': options,
            'help': help_text,
            'required': required
        }
        
        # Add validators
        validators = []
        if required:
            validators.append(lambda v: FormValidator.validate_required_field(v, label))
        
        self.validators[key] = validators
        return self
    
    def add_multiselect(self, key: str, label: str, options: List[str], help_text: str = "", 
                       required: bool = False) -> 'FormBuilder':
        """Add multiselect field."""
        self.fields[key] = {
            'type': 'multiselect',
            'label': label,
            'options': options,
            'help': help_text,
            'required': required
        }
        
        # Add validators
        validators = []
        if required:
            validators.append(lambda v: (len(v) > 0, f"{label} must have at least one selection"))
        
        self.validators[key] = validators
        return self
    
    def add_number_input(self, key: str, label: str, min_value: Optional[float] = None, 
                        max_value: Optional[float] = None, help_text: str = "", 
                        required: bool = False) -> 'FormBuilder':
        """Add number input field."""
        self.fields[key] = {
            'type': 'number_input',
            'label': label,
            'min_value': min_value,
            'max_value': max_value,
            'help': help_text,
            'required': required
        }
        
        # Add validators
        validators = []
        if required:
            validators.append(lambda v: FormValidator.validate_required_field(v, label))
        if min_value is not None or max_value is not None:
            validators.append(lambda v: FormValidator.validate_numeric_range(v, min_value, max_value))
        
        self.validators[key] = validators
        return self
    
    def add_checkbox(self, key: str, label: str, help_text: str = "") -> 'FormBuilder':
        """Add checkbox field."""
        self.fields[key] = {
            'type': 'checkbox',
            'label': label,
            'help': help_text
        }
        
        self.validators[key] = []
        return self
    
    def add_file_uploader(self, key: str, label: str, allowed_types: List[str], 
                         help_text: str = "", required: bool = False) -> 'FormBuilder':
        """Add file uploader field."""
        self.fields[key] = {
            'type': 'file_uploader',
            'label': label,
            'allowed_types': allowed_types,
            'help': help_text,
            'required': required
        }
        
        # Add validators
        validators = []
        if required:
            validators.append(lambda v: FormValidator.validate_required_field(v, label))
        
        self.validators[key] = validators
        return self
    
    def render(self) -> Dict[str, Any]:
        """Render the form and return form data."""
        form_data = {}
        
        with st.form(self.form_key):
            # Render all fields
            for key, field_config in self.fields.items():
                field_type = field_config['type']
                
                if field_type == 'text_input':
                    form_data[key] = st.text_input(
                        field_config['label'],
                        placeholder=field_config['placeholder'],
                        help=field_config['help'],
                        key=f"{self.form_key}_{key}"
                    )
                
                elif field_type == 'text_area':
                    form_data[key] = st.text_area(
                        field_config['label'],
                        placeholder=field_config['placeholder'],
                        help=field_config['help'],
                        height=field_config['height'],
                        key=f"{self.form_key}_{key}"
                    )
                
                elif field_type == 'selectbox':
                    form_data[key] = st.selectbox(
                        field_config['label'],
                        field_config['options'],
                        help=field_config['help'],
                        key=f"{self.form_key}_{key}"
                    )
                
                elif field_type == 'multiselect':
                    form_data[key] = st.multiselect(
                        field_config['label'],
                        field_config['options'],
                        help=field_config['help'],
                        key=f"{self.form_key}_{key}"
                    )
                
                elif field_type == 'number_input':
                    form_data[key] = st.number_input(
                        field_config['label'],
                        min_value=field_config['min_value'],
                        max_value=field_config['max_value'],
                        help=field_config['help'],
                        key=f"{self.form_key}_{key}"
                    )
                
                elif field_type == 'checkbox':
                    form_data[key] = st.checkbox(
                        field_config['label'],
                        help=field_config['help'],
                        key=f"{self.form_key}_{key}"
                    )
                
                elif field_type == 'file_uploader':
                    form_data[key] = st.file_uploader(
                        field_config['label'],
                        type=field_config['allowed_types'],
                        help=field_config['help'],
                        key=f"{self.form_key}_{key}"
                    )
            
            # Submit button
            submitted = st.form_submit_button("Submit")
            
            if submitted:
                # Validate form data
                is_valid, validation_errors = self.validate_form_data(form_data)
                
                if is_valid:
                    return form_data
                else:
                    # Show validation errors
                    for error in validation_errors:
                        st.error(error)
                    return {}
        
        return {}
    
    def validate_form_data(self, form_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate form data using configured validators."""
        errors = []
        
        for key, value in form_data.items():
            if key in self.validators:
                for validator in self.validators[key]:
                    is_valid, error_msg = validator(value)
                    if not is_valid:
                        errors.append(error_msg)
        
        return len(errors) == 0, errors


def create_confirmation_dialog(title: str, message: str, confirm_text: str = "Confirm", 
                             cancel_text: str = "Cancel") -> bool:
    """Create a confirmation dialog."""
    dialog_key = f"confirm_dialog_{uuid.uuid4().hex[:8]}"
    
    with st.container():
        st.warning(f"**{title}**")
        st.write(message)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(confirm_text, key=f"{dialog_key}_confirm", type="primary"):
                return True
        
        with col2:
            if st.button(cancel_text, key=f"{dialog_key}_cancel"):
                return False
    
    return False


def create_progress_form(steps: List[str], current_step: int = 0) -> None:
    """Create a progress indicator for multi-step forms."""
    if not steps:
        return
    
    # Progress bar
    progress = (current_step + 1) / len(steps)
    st.progress(progress)
    
    # Step indicator
    st.write(f"Step {current_step + 1} of {len(steps)}: {steps[current_step]}")
    
    # Step navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if current_step > 0:
            st.button("← Previous", key="prev_step")
    
    with col3:
        if current_step < len(steps) - 1:
            st.button("Next →", key="next_step")


def sanitize_input(text: str, max_length: int = 10000, remove_html: bool = True) -> str:
    """Sanitize user input for security."""
    if not text:
        return ""
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove HTML tags if requested
    if remove_html:
        text = re.sub(r'<[^>]+>', '', text)
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def format_validation_errors(errors: List[str]) -> str:
    """Format validation errors for display."""
    if not errors:
        return ""
    
    if len(errors) == 1:
        return f"❌ {errors[0]}"
    
    formatted = "❌ Please fix the following errors:\n"
    for i, error in enumerate(errors, 1):
        formatted += f"{i}. {error}\n"
    
    return formatted


def create_dynamic_form(form_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a form dynamically from configuration."""
    form_key = form_config.get('form_key', f'dynamic_form_{uuid.uuid4().hex[:8]}')
    form_title = form_config.get('title', 'Form')
    
    st.subheader(form_title)
    
    form_data = {}
    
    with st.form(form_key):
        fields = form_config.get('fields', [])
        
        for field in fields:
            field_type = field.get('type', 'text_input')
            field_key = field.get('key', f'field_{len(form_data)}')
            field_label = field.get('label', 'Field')
            
            if field_type == 'text_input':
                form_data[field_key] = st.text_input(
                    field_label,
                    value=field.get('default', ''),
                    placeholder=field.get('placeholder', ''),
                    help=field.get('help', ''),
                    key=f"{form_key}_{field_key}"
                )
            
            elif field_type == 'text_area':
                form_data[field_key] = st.text_area(
                    field_label,
                    value=field.get('default', ''),
                    placeholder=field.get('placeholder', ''),
                    help=field.get('help', ''),
                    height=field.get('height', 100),
                    key=f"{form_key}_{field_key}"
                )
            
            elif field_type == 'selectbox':
                options = field.get('options', [])
                default_index = 0
                if field.get('default') in options:
                    default_index = options.index(field.get('default'))
                
                form_data[field_key] = st.selectbox(
                    field_label,
                    options,
                    index=default_index,
                    help=field.get('help', ''),
                    key=f"{form_key}_{field_key}"
                )
            
            elif field_type == 'multiselect':
                form_data[field_key] = st.multiselect(
                    field_label,
                    field.get('options', []),
                    default=field.get('default', []),
                    help=field.get('help', ''),
                    key=f"{form_key}_{field_key}"
                )
            
            elif field_type == 'checkbox':
                form_data[field_key] = st.checkbox(
                    field_label,
                    value=field.get('default', False),
                    help=field.get('help', ''),
                    key=f"{form_key}_{field_key}"
                )
            
            elif field_type == 'number_input':
                form_data[field_key] = st.number_input(
                    field_label,
                    value=field.get('default', 0),
                    min_value=field.get('min_value'),
                    max_value=field.get('max_value'),
                    help=field.get('help', ''),
                    key=f"{form_key}_{field_key}"
                )
        
        # Submit button
        submit_label = form_config.get('submit_label', 'Submit')
        submitted = st.form_submit_button(submit_label)
        
        if submitted:
            # Validate if validation rules are provided
            validation_rules = form_config.get('validation', {})
            if validation_rules:
                is_valid, errors = validate_dynamic_form(form_data, validation_rules)
                if not is_valid:
                    for error in errors:
                        st.error(error)
                    return {}
            
            return form_data
    
    return {}


def validate_dynamic_form(form_data: Dict[str, Any], validation_rules: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate dynamic form data."""
    errors = []
    
    for field_key, rules in validation_rules.items():
        if field_key not in form_data:
            continue
        
        value = form_data[field_key]
        
        # Required validation
        if rules.get('required', False):
            is_valid, error = FormValidator.validate_required_field(value, field_key)
            if not is_valid:
                errors.append(error)
        
        # Length validation
        if 'min_length' in rules or 'max_length' in rules:
            min_len = rules.get('min_length', 0)
            max_len = rules.get('max_length', 10000)
            is_valid, error = FormValidator.validate_text_length(value, min_len, max_len)
            if not is_valid:
                errors.append(error)
        
        # Email validation
        if rules.get('type') == 'email':
            is_valid, error = FormValidator.validate_email(value)
            if not is_valid:
                errors.append(error)
        
        # URL validation
        if rules.get('type') == 'url':
            is_valid, error = FormValidator.validate_url(value)
            if not is_valid:
                errors.append(error)
    
    return len(errors) == 0, errors


def create_search_form(placeholder: str = "Search...", help_text: str = "") -> str:
    """Create a simple search form."""
    search_key = f"search_{uuid.uuid4().hex[:8]}"
    
    with st.form(search_key):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            search_query = st.text_input(
                "Search",
                placeholder=placeholder,
                help=help_text,
                label_visibility="collapsed",
                key=f"{search_key}_input"
            )
        
        with col2:
            submitted = st.form_submit_button("🔍 Search")
        
        if submitted and search_query.strip():
            return search_query.strip()
    
    return ""