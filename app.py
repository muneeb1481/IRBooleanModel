import streamlit as st
from nltk.stem.porter import PorterStemmer

# Initialize Porter Stemmer
stem_tool = PorterStemmer()

def check_query_validity(user_input):
    user_input = user_input.lower().strip()  # Remove extra spaces and convert to lowercase
    if not user_input:
        return None, None, False

    input_words = user_input.split()
    if len(input_words) > 5:
        return None, None, False

    for word in input_words:
        if not word.isalpha() and word not in {"and", "or", "not"}:
            return None, None, False

    valid_operators = {"and", "or", "not"}
    for idx in range(len(input_words)):
        if idx % 2 == 1:  # Operators should be at odd positions
            if input_words[idx] not in valid_operators:
                return None, None, False
        elif idx % 2 == 0:  # Terms should be at even positions
            if input_words[idx] in valid_operators:
                return None, None, False

    processed_terms = [stem_tool.stem(word) for word in input_words if word not in valid_operators]
    extracted_ops = [word for word in input_words if word in valid_operators]

    return processed_terms, extracted_ops, True


def fetch_matching_docs(query_terms, query_ops, term_to_docs_map):
    all_documents = set()
    for doc_list in term_to_docs_map.values():
        all_documents.update(doc_list)

    if len(query_terms) == 1:
        if query_terms[0] in term_to_docs_map:
            return term_to_docs_map[query_terms[0]]
        else:
            return []
    elif len(query_terms) == 2:
        list1 = term_to_docs_map.get(query_terms[0], [])
        list2 = term_to_docs_map.get(query_terms[1], [])
        if not list1 or not list2:
            return []

        if query_ops[0] == "and":
            return list(set(list1) & set(list2))  # Intersection
        elif query_ops[0] == "or":
            return list(set(list1) | set(list2))  # Union
        elif query_ops[0] == "not":
            return list(set(list1) - set(list2))  # Difference
    elif len(query_terms) == 3:
        list1 = term_to_docs_map.get(query_terms[0], [])
        list2 = term_to_docs_map.get(query_terms[1], [])
        list3 = term_to_docs_map.get(query_terms[2], [])
        if not list1 or not list2 or not list3:
            return []

        # Logical rule: (term1 op1 term2) op2 term3
        if query_ops[0] == "and" and query_ops[1] == "and":
            return list(set(list1) & set(list2) & set(list3))
        elif query_ops[0] == "and" and query_ops[1] == "or":
            return list((set(list1) & set(list2)) | set(list3))
        elif query_ops[0] == "or" and query_ops[1] == "and":
            return list((set(list1) | set(list2)) & set(list3))
        elif query_ops[0] == "or" and query_ops[1] == "or":
            return list(set(list1) | set(list2) | set(list3))
        elif query_ops[0] == "and" and query_ops[1] == "not":
            return list(set(list1) & (set(list2) - set(list3)))
        elif query_ops[0] == "or" and query_ops[1] == "not":
            return list((set(list1) | set(list2)) - set(list3))
        elif query_ops[0] == "not" and query_ops[1] == "and":
            return list((all_documents - set(list1)) & set(list3))
        elif query_ops[0] == "not" and query_ops[1] == "or":
            return list((all_documents - set(list1)) | set(list3))
        elif query_ops[0] == "not" and query_ops[1] == "not":
            return list(all_documents - set(list1) - set(list2))

    return []


def validate_proximity_query(user_input):
    user_input = user_input.lower().strip()  # Remove extra spaces and convert to lowercase
    if not user_input:
        return (), False

    input_words = user_input.split()
    if len(input_words) != 2:
        return (), False

    for word in input_words:
        if not word.isalpha():
            return (), False

    processed_terms = tuple(stem_tool.stem(word) for word in input_words)
    return processed_terms, True


def perform_proximity_search(query_terms, max_distance, term_positions_map):
    term1, term2 = query_terms
    if term1 not in term_positions_map or term2 not in term_positions_map:
        return []

    matching_docs = set()
    for doc in term_positions_map[term1].keys() & term_positions_map[term2].keys():  # Common documents
        positions1 = sorted(term_positions_map[term1][doc])
        positions2 = sorted(term_positions_map[term2][doc])

        idx1, idx2 = 0, 0
        while idx1 < len(positions1) and idx2 < len(positions2):
            if abs(positions1[idx1] - positions2[idx2]) <= max_distance:
                matching_docs.add(doc)
                idx1 += 1
            elif positions1[idx1] < positions2[idx2]:
                idx1 += 1
            else:
                idx2 += 1

    return list(matching_docs)

def load_index_data(file_path):
    index_map = {}
    with open(file_path, 'r') as file:
        for line in file:
            term, doc_ids = line.strip().split(' : ')
            index_map[term] = eval(doc_ids)
    return index_map

# Load indices
term_to_docs_map = load_index_data('inverted_index.txt')
term_positions_map = load_index_data('positional_index.txt')

# Streamlit App Design
st.title("🔍 Boolean and Proximity Search Model")
st.markdown("Developed by: **Muneeb Ur Rehman**")
st.markdown("<hr style='border:1px solid #ddd'>", unsafe_allow_html=True)

# Boolean Query Section
st.markdown("### 📝 Boolean Query Search")
st.markdown("""
**Rules for Boolean Queries:**
1. Use **AND**, **OR**, or **NOT** operators.
2. Maximum of **5 words** including operators.
3. Only **alphabets** are allowed in terms.
""")

boolean_query_input = st.text_input("Enter your Boolean query:")
if st.button("Search Boolean Query"):
    if not boolean_query_input:
        st.error("Query cannot be empty.")
    else:
        input_words = boolean_query_input.strip().split()
        if len(input_words) > 5:
            st.error("Only 5 words allowed at maximum.")
        elif not all(word.isalpha() for word in input_words if word.lower() not in {"and", "or", "not"}):
            st.error("Only alphabets allowed in terms.")
        else:
            query_terms, query_ops, is_valid = check_query_validity(boolean_query_input)
            if is_valid:
                results = fetch_matching_docs(query_terms, query_ops, term_to_docs_map)
                if results:
                    st.success("**✅ Documents Found:**")
                    for idx, doc in enumerate(results):
                        st.write(f"📄 Document {idx + 1}: {doc}")
                else:
                    st.warning("No documents found.")
            else:
                st.error("Invalid query format. Please follow the rules.")

st.markdown("<hr style='border:1px solid #ddd'>", unsafe_allow_html=True)

# Proximity Query Section
st.markdown("### 📝 Proximity Query Search")
st.markdown("""
**Rules for Proximity Queries:**
1. Enter **exactly two words**.
2. Only **alphabets** are allowed in terms.
3. Specify the maximum distance (**K**) between the two words.
""")

proximity_query_input = st.text_input("Enter your proximity query:")
k_value = st.number_input("Enter the value of K (maximum distance):", min_value=1, step=1, format="%d")
if st.button("Search Proximity Query"):
    if not proximity_query_input:
        st.error("Query cannot be empty.")
    else:
        input_words = proximity_query_input.strip().split()
        if len(input_words) != 2:
            st.error("Enter exactly two words.")
        elif not all(word.isalpha() for word in input_words):
            st.error("Only alphabets allowed in terms.")
        else:
            query_terms, is_valid = validate_proximity_query(proximity_query_input)
            if is_valid:
                results = perform_proximity_search(query_terms, k_value, term_positions_map)
                if results:
                    st.success("**✅ Documents Found:**")
                    for idx, doc in enumerate(results):
                        st.write(f"📄 Document {idx + 1}: {doc}")
                else:
                    st.warning("No documents found.")
            else:
                st.error("Invalid query format. Please follow the rules.")