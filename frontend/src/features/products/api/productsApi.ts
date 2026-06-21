import { apiRequest } from "../../../api/http";
import type { Product, ProductCategory } from "../types/productTypes";

export function getCategories(): Promise<ProductCategory[]> {
  return apiRequest<ProductCategory[]>("/api/v1/catalog/categories");
}

export function getProducts(): Promise<Product[]> {
  return apiRequest<Product[]>("/api/v1/catalog/products");
}
