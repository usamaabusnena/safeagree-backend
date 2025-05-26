from io import BytesIO
import PyPDF2
from docx import Document

class FileReaderService:
    def __init__(self):
        print("FileReaderService initialized.")

    def _read_policy_file(self, file_content: bytes, file_extension: str = 'txt') -> str:
        """
        Reads policy text from uploaded file content.
        This function is designed to handle different file types (e.g., .txt, .pdf, .docx)
        by attempting to extract plain text.

        Args:
            file_content: The raw byte content of the uploaded file.
            file_extension: The extension of the file (e.g., 'txt', 'pdf', 'docx').
                            Used to determine the appropriate parsing method.

        Returns:
            The extracted plain text content of the policy, or an empty string if extraction fails.
        """
        print(f"Attempting to read text from uploaded file with extension: {file_extension}")
        extracted_text = ""

        try:
            if file_extension.lower() == 'txt':
                # Assume UTF-8 encoding for text files
                extracted_text = file_content.decode('utf-8')
                print("Successfully read text from .txt file.")
            # --- CONCEPTUAL IMPLEMENTATION FOR OTHER FILE TYPES (UNCOMMENT AND CONFIGURE) ---
            elif file_extension.lower() == 'pdf':
            # Requires PyPDF2
                # Create a BytesIO object from the file_content to read it as a file
                pdf_file = BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    extracted_text += page.extract_text() + "\n"
                print("Successfully extracted text from .pdf file.")
            elif file_extension.lower() == 'docx':
            # Requires python-docx
                # Create a BytesIO object from the file_content
                doc_file = BytesIO(file_content)
                document = Document(doc_file)
                for paragraph in document.paragraphs:
                    extracted_text += paragraph.text + "\n"
                print("Successfully extracted text from .docx file.")
            else:
                print(f"Unsupported file type for reading: {file_extension}. Attempting to decode as UTF-8.")
                # Fallback for unknown types, try to decode as plain text
                try:
                    extracted_text = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    print("Could not decode file content as UTF-8. Trying latin-1.")
                    extracted_text = file_content.decode('latin-1') # Another common fallback
                print("Attempted to read as plain text.")

        except Exception as e:
            print(f"Error reading file content for extension {file_extension}: {e}")
            extracted_text = "" # Return empty string on error

        return extracted_text.strip() # Strip leading/trailing whitespace from final text
