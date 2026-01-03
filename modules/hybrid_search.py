import re
from typing import List, Dict
from modules.embeddings_manager import search_similar, collection

def extract_keywords(query: str) -> List[str]:
    """
    Extrae palabras clave importantes de la pregunta
    """
    # Palabras comunes a ignorar
    stopwords = {
        'el', 'la', 'de', 'en', 'y', 'a', 'que', 'es', 'por', 'un', 'una',
        'con', 'para', 'como', 'del', 'los', 'las', 'al', 'lo', 'se', 'su',
        'qué', 'cuál', 'cuáles', 'cómo', 'dónde', 'quién', 'cuándo', 'cuánto'
    }
    
    # Extraer palabras
    words = re.findall(r'\w+', query.lower())
    
    # Filtrar stopwords y palabras cortas
    keywords = [w for w in words if w not in stopwords and len(w) > 3]
    
    return keywords

def keyword_search_in_chunks(keywords: List[str], all_documents: List[str]) -> List[int]:
    """
    Busca keywords en los documentos y retorna índices que los contienen
    """
    matching_indices = []
    
    for idx, doc in enumerate(all_documents):
        doc_lower = doc.lower()
        
        # Contar cuántas keywords aparecen
        matches = sum(1 for kw in keywords if kw in doc_lower)
        
        if matches > 0:
            matching_indices.append((idx, matches))
    
    # Ordenar por número de matches (descendente)
    matching_indices.sort(key=lambda x: x[1], reverse=True)
    
    return [idx for idx, _ in matching_indices]

def hybrid_search(query: str, top_k: int = 7, doc_id: str = None) -> Dict:
    """
    Búsqueda híbrida: combina semántica + keywords
    """
    
    # 1. Búsqueda semántica (principal)
    semantic_results = search_similar(query, top_k=top_k, doc_id=doc_id)
    
    # 2. Extraer keywords de la pregunta
    keywords = extract_keywords(query)
    
    if not keywords:
        # Si no hay keywords, retornar solo resultados semánticos
        return semantic_results
    
    # 3. Obtener todos los documentos de la colección
    try:
        if doc_id:
            all_items = collection.get(where={"doc_id": doc_id})
        else:
            all_items = collection.get()
        
        all_documents = all_items.get('documents', [])
        all_metadatas = all_items.get('metadatas', [])
        all_ids = all_items.get('ids', [])
        
        if not all_documents:
            return semantic_results
        
        # 4. Buscar por keywords
        keyword_indices = keyword_search_in_chunks(keywords, all_documents)
        
        # 5. Combinar resultados
        # Índices de resultados semánticos
        semantic_docs = semantic_results.get('documents', [[]])[0]
        semantic_metas = semantic_results.get('metadatas', [[]])[0]
        
        # Crear set de documentos ya incluidos (para evitar duplicados)
        included_docs = set(semantic_docs)
        
        # Agregar hasta 3 documentos adicionales basados en keywords
        extra_docs = []
        extra_metas = []
        added = 0
        
        for idx in keyword_indices:
            if added >= 3:  # Máximo 3 adicionales
                break
            
            doc = all_documents[idx]
            if doc not in included_docs:
                extra_docs.append(doc)
                extra_metas.append(all_metadatas[idx])
                included_docs.add(doc)
                added += 1
        
        # Combinar: primero semánticos, luego keywords
        combined_docs = semantic_docs + extra_docs
        combined_metas = semantic_metas + extra_metas
        
        print(f"🔍 Híbrido: {len(semantic_docs)} semánticos + {len(extra_docs)} por keywords")
        
        return {
            'documents': [combined_docs],
            'metadatas': [combined_metas],
            'distances': semantic_results.get('distances', [[]]),
            'ids': semantic_results.get('ids', [[]])
        }
    
    except Exception as e:
        print(f"⚠️ Error en búsqueda híbrida: {e}")
        return semantic_results

def smart_search(query: str, doc_id: str = None) -> Dict:
    """
    Búsqueda inteligente que decide estrategia según la pregunta
    """
    
    query_lower = query.lower()
    
    # Detectar si busca algo muy específico (número, fecha, nombre exacto)
    has_number = bool(re.search(r'\d{3,}', query))  # 3+ dígitos consecutivos
    has_date = bool(re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', query))
    
    # Si busca algo muy específico, aumentar fragmentos y usar híbrido
    if has_number or has_date:
        print("🎯 Búsqueda específica detectada (número/fecha)")
        return hybrid_search(query, top_k=10, doc_id=doc_id)
    
    # Para preguntas generales, usar híbrido estándar
    return hybrid_search(query, top_k=7, doc_id=doc_id)